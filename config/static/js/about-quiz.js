(function () {
  "use strict";
  var root = document.querySelector("[data-about-quiz]");
  if (!root) return;
  var content = root.querySelector("[data-quiz-content]");
  var questions = [
    ["Чем были наши домики раньше?", ["Коттеджами", "Морскими контейнерами", "Железнодорожными вагонами"], 1, "Это морские контейнеры. Мы утеплили их, вставили окна во всю стену и пристроили террасы — теперь изнутри ни за что не догадаться, с чего всё начиналось."],
    ["Как называется речка на глэмпинге?", ["Ока", "Скнижка", "Нара"], 1, "Наша «Скнижка» — та самая река, что течёт мимо ваших террас. Первые упоминания о ней есть в книжках, которым уже 300+ лет."],
    ["Усадьба какого известного художника находится ближе всего к глэмпингу?", ["Исаака Левитана", "Ивана Шишкина", "Василия Поленова"], 2, "В. Поленов посвятил почти половину своей жизни этому месту — живописному берегу Оки. А Шишкин и Левитан были частыми гостями и близкими друзьями художника."],
    ["Кого из животных на нашей Ферме больше всего?", ["Овец", "Павлинов", "Коров"], 0, "Овец около сотни. Коровы, козы, гуси, утки и кролики тоже есть, но их намного меньше. Павлинов пока не заводили)"],
    ["Когда в Поленово цветёт «тульская сакура»?", ["Апрель", "Май", "Июнь"], 1, "Декоративная сакура, которую Поленов сажал лично, цветёт в начале мая ~ 10 дней — и ради этого сюда приезжают отдельно."],
    ["Что такое «Корабль» на глэмпинге?", ["Большая беседка", "Ресторан", "Магазин"], 0, "«Корабль» — так мы прозвали нашу любимую большую беседку. Стоит он прямо на берегу Скнижки и небольшой плотины, а сзади красуется настоящее водяное колесо, сделанное руками нашего дедушки."]
  ];
  var praise = ["Супер!", "Верно!", "Отлично!", "Всё так!", "Точно!", "В точку!", "Браво!", "Именно так!", "Молодцы!", "Попадание!"];
  var index = 0, score = 0;
  function scoreText() {
    return score + "/" + questions.length;
  }
  function element(tag, text, cls) {
    var node = document.createElement(tag);
    node.textContent = text;
    if (cls) node.className = cls;
    return node;
  }
  function render(moveFocus) {
    content.replaceChildren();
    if (index === questions.length) {
      content.appendChild(element("p", scoreText(), "about-quiz__score about-quiz__score--final"));
      content.appendChild(element("h3", score === questions.length ? "Всё абсолютно точно!" : "Спасибо за игру!", "about-quiz__question"));
      content.appendChild(element("p", "Кажется, вы у нас уже были)", "about-quiz__story"));
      var actions = element("div", "", "about-quiz__actions");
      var book = element("button", "Свободные даты", "btn btn--primary");
      book.type = "button";
      book.setAttribute("data-booking-open", "");
      book.setAttribute("data-entry-point", "7");
      actions.appendChild(book);
      var reset = element("button", "Начать заново", "btn btn--outline");
      reset.type = "button";
      reset.addEventListener("click", function () { index = 0; score = 0; render(true); });
      actions.appendChild(reset);
      content.appendChild(actions);
      if (moveFocus) book.focus();
      return;
    }
    var question = questions[index];
    content.appendChild(element("p", "Вопрос " + (index + 1) + " из " + questions.length));
    var counter = element("p", "Правильных ответов: " + scoreText(), "about-quiz__score");
    content.appendChild(counter);
    content.appendChild(element("h3", question[0], "about-quiz__question"));
    var options = element("div", "", "about-quiz__options");
    question[1].forEach(function (label, i) {
      var button = element("button", label, "btn btn--outline");
      button.type = "button";
      button.addEventListener("click", function () {
        if (button.disabled) return;
        var correct = i === question[2];
        if (correct) {
          score++;
          counter.textContent = "Правильных ответов: " + scoreText();
        }
        button.classList.add(correct ? "about-quiz__answer--correct" : "about-quiz__answer--incorrect");
        button.setAttribute("aria-label", label + (correct ? " — верно" : " — неверно"));
        options.querySelectorAll("button").forEach(function (b) { b.disabled = true; });
        var feedback = correct ? praise[Math.floor(Math.random() * praise.length)] : question[3];
        content.appendChild(element("p", feedback, "about-quiz__story"));
        var next = element("button", index === questions.length - 1 ? "Узнать результат" : "Следующий вопрос", "btn btn--primary");
        next.type = "button";
        next.addEventListener("click", function () { index++; render(true); });
        content.appendChild(next);
        next.focus();
      }, { once: true });
      options.appendChild(button);
    });
    content.appendChild(options);
    if (moveFocus && options.firstElementChild) options.firstElementChild.focus();
  }
  render();
}());
