'use strict';

// A throttled/error page must never be measured as the site's layout.
module.exports = async function navigate(page, url) {
  for (let attempt = 1; attempt <= 3; attempt++) {
    const response = await page.goto(url);
    if (response && response.status() === 200) {
      await page.waitForTimeout(500);
      return response;
    }
    const status = response ? response.status() : 'no response';
    if (![429, 502, 503, 504].includes(status) || attempt === 3) {
      throw new Error(`Navigation failed: HTTP ${status}, ${url}`);
    }
    console.log(`HTTP ${status}: pause before retrying ${url}`);
    await page.waitForTimeout(30000);
  }
};
