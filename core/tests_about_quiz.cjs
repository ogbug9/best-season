const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

const script = fs.readFileSync(path.join(__dirname, '../config/static/js/about-quiz.js'), 'utf8');

function createQuiz() {
  let focused;
  class Element {
    constructor(tag) { this.tagName = tag; this.children = []; this.attrs = {}; this.events = {}; this.disabled = false; }
    setAttribute(name, value) { this.attrs[name] = value; }
    appendChild(child) { this.children.push(child); return child; }
    replaceChildren() { this.children = []; }
    get firstElementChild() { return this.children[0]; }
    querySelectorAll(selector) { return selector === 'button' ? this.children.filter(child => child.tagName === 'button') : []; }
    addEventListener(name, fn) { this.events[name] = fn; }
    focus() { focused = this; }
    click() { if (!this.disabled && this.events.click) this.events.click(); }
  }
  const content = new Element('div');
  const root = { querySelector: () => content };
  const document = { querySelector: () => root, createElement: tag => new Element(tag) };
  vm.runInNewContext(script, { document });
  return { content, get focused() { return focused; } };
}

for (const [name, correctCount, expected] of [
  ['все правильные', 6, 'Кажется, вы у нас уже были'],
  ['пять правильных', 5, 'Кажется, вы у нас уже были'],
  ['четыре правильных', 4, 'Почти свой'],
  ['три правильных', 3, 'Почти свой'],
  ['два правильных', 2, 'Самое время приехать и всё увидеть'],
  ['один правильный', 1, 'Самое время приехать и всё увидеть'],
  ['без правильных', 0, 'Самое время приехать и всё увидеть'],
]) {
  test('викторина: ' + name, () => {
    const quiz = createQuiz();
    const correct = [1, 1, 2, 0, 1, 0];
    for (let i = 0; i < 6; i++) {
      assert.equal(quiz.content.children[0].textContent, `Вопрос ${i + 1} из 6`);
      const options = quiz.content.children[2].children;
      const selected = i < correctCount ? correct[i] : (correct[i] + 1) % 3;
      options[selected].click();
      assert.equal(quiz.content.children[3].className, 'about-quiz__story');
      assert.ok(options.every(option => option.disabled));
      assert.ok(options[selected].className.includes(i < correctCount ? 'about-quiz__answer--correct' : 'about-quiz__answer--incorrect'));
      options[selected].click();
      assert.equal(quiz.content.children.length, 5);
      const next = quiz.content.children[4];
      assert.equal(quiz.focused, next);
      next.click();
    }
    assert.equal(quiz.content.children[0].textContent, expected);
    const book = quiz.content.children[1];
    assert.equal(book.textContent, 'Свободные даты');
    assert.ok(Object.hasOwn(book.attrs, 'data-booking-open'));
    assert.equal(book.attrs['data-entry-point'], '7');
    assert.equal(quiz.focused, book);
    quiz.content.children[2].click();
    assert.equal(quiz.content.children[0].textContent, 'Вопрос 1 из 6');
  });
}
