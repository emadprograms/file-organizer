import { describe, it, expect, afterEach } from 'vitest';

describe('Initial UI Component Test', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('verifies basic DOM rendering in JSDOM', () => {
    document.body.innerHTML = '<div>Hello World</div>';
    const div = document.querySelector('div');
    expect(div.textContent).toBe('Hello World');
  });
});
