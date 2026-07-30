import { defineConfig, devices } from '@playwright/test';

/**
 * Browser gates for the judge journey.
 *
 * Two projects, not one, because the two viewports are the actual requirement:
 * 1440x900 is the demo machine and 1366x768 is the smallest screen the judges
 * might sit us at, and "nothing critical is cut" only means something when it is
 * measured at a stated size.
 *
 * Deliberately no screenshot baselines. The results workspace renders a WebGL
 * canvas, so a committed baseline would encode this machine's GPU and font
 * rasterisation and go red on anyone else's - and a red gate over two pixels of
 * antialiasing during competition week costs more than it protects. Everything
 * the plan asks these gates to prove - frozen copy, the calculated label, the
 * non-certification sentence, the synthetic viewer label, document width - is
 * observable in the DOM, so that is where it is asserted.
 *
 * Serves the production build rather than `next dev`: the demo runs on
 * `next start`, and the frozen route verifies artifact hashes, which is only
 * meaningful against the files a real build emits.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:3100',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'desktop-1440',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'laptop-1366',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1366, height: 768 } },
    },
  ],
  webServer: {
    // Port 3100, not 3000: the judge demo launcher owns 3000, and a gate run that
    // fights it either fails for the wrong reason or kills a live demo.
    command: 'node demo-server.cjs',
    env: { PORT: '3100', HOSTNAME: '127.0.0.1' },
    url: 'http://127.0.0.1:3100/demo',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
