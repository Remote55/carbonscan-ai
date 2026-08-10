/**
 * The screens a user sees when something breaks.
 *
 * There were none: any thrown error reached Next.js's production fallback,
 * "Application error: a client-side exception has occurred", with no retry and
 * nothing to quote in a bug report. These assert the properties that make the
 * difference — a way back, something to retry with, and an identifier that
 * ties the screen to a server log line.
 *
 * Rendered with renderToStaticMarkup, like the rest of this suite: there is no
 * jsdom environment configured, and adding one to check that a React onClick
 * fires would be testing React rather than this app.
 */

import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import PageError from './error';
import GlobalErrorScreen from './global-error';
import NotFoundScreen from './not-found';

function withDigest(message: string, digest?: string) {
  return Object.assign(new Error(message), digest ? { digest } : {});
}

describe('page error boundary', () => {
  it('offers a retry control and a route back into the site', () => {
    const markup = renderToStaticMarkup(
      <PageError error={withDigest('boom')} reset={() => undefined} />,
    );

    expect(markup).toContain('ลองใหม่');
    expect(markup).toMatch(/<a\b[^>]*href="\/"/);
  });

  it('shows the digest, the only handle on the server log line', () => {
    const markup = renderToStaticMarkup(
      <PageError error={withDigest('boom', 'e3f19a2b')} reset={() => undefined} />,
    );

    expect(markup).toContain('e3f19a2b');
    expect(markup).toContain('รหัสอ้างอิง');
  });

  it('never prints the exception message, which can carry internals', () => {
    const markup = renderToStaticMarkup(
      <PageError
        error={withDigest('connect ECONNREFUSED 10.0.0.4:5432', 'abc')}
        reset={() => undefined}
      />,
    );

    expect(markup).not.toContain('ECONNREFUSED');
    expect(markup).not.toContain('10.0.0.4');
  });

  it('omits the reference line entirely when there is no digest', () => {
    const markup = renderToStaticMarkup(
      <PageError error={withDigest('boom')} reset={() => undefined} />,
    );

    // An empty "รหัสอ้างอิง:" invites the user to quote nothing.
    expect(markup).not.toContain('รหัสอ้างอิง');
  });
});

describe('not found', () => {
  it('names the status and links home', () => {
    const markup = renderToStaticMarkup(<NotFoundScreen />);

    expect(markup).toContain('404');
    expect(markup).toMatch(/<a\b[^>]*href="\/"/);
  });
});

describe('global error boundary', () => {
  it('renders its own document, because the failing layout cannot supply one', () => {
    const markup = renderToStaticMarkup(
      <GlobalErrorScreen error={withDigest('boom', 'zz99')} reset={() => undefined} />,
    );

    expect(markup).toContain('<html');
    expect(markup).toContain('<body');
    expect(markup).toContain('ลองใหม่');
    expect(markup).toContain('zz99');
  });

  it('styles itself inline, since globals.css may be what failed to load', () => {
    const markup = renderToStaticMarkup(
      <GlobalErrorScreen error={withDigest('boom')} reset={() => undefined} />,
    );

    expect(markup).toMatch(/<body[^>]*style="/);
    // A class name here would be a dependency on a stylesheet this screen
    // exists precisely because it cannot count on.
    expect(markup).not.toMatch(/<body[^>]*class=/);
  });
});
