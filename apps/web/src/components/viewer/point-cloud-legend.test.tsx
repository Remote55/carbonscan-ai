import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { PointCloudLegend } from './point-cloud-legend';

describe('PointCloudLegend', () => {
  it('gives every decorative color swatch a high-contrast boundary', () => {
    const markup = renderToStaticMarkup(<PointCloudLegend />);
    const swatches = [...markup.matchAll(/<span[^>]*aria-hidden="true"[^>]*class="([^"]+)"/g)];

    expect(swatches).toHaveLength(3);
    for (const [, classes] of swatches) {
      expect(classes.split(' ')).toEqual(
        expect.arrayContaining(['size-3', 'border-2', 'border-paper']),
      );
    }
  });
});
