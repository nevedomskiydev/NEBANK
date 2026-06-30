// Mini App localization (RU/EN). No emoji anywhere (TZ §17).
export type Lang = "ru" | "en";

export const DICT: Record<string, { ru: string; en: string }> = {
  // nav
  nav_home: { ru: "Главная", en: "Home" },
  nav_history: { ru: "История", en: "History" },
  nav_budgets: { ru: "Бюджеты", en: "Budgets" },
  nav_rates: { ru: "Курсы", en: "Rates" },
  nav_more: { ru: "Ещё", en: "More" },

  // dashboard
  balance: { ru: "Баланс", en: "Balance" },
  income: { ru: "Доход", en: "Income" },
  expense: { ru: "Расход", en: "Expense" },
  net: { ru: "Итог", en: "Net" },
  spent: { ru: "Потрачено", en: "Spent" },
  this_today: { ru: "Сегодня", en: "Today" },
  this_week: { ru: "Неделя", en: "Week" },
  this_month: { ru: "Месяц", en: "Month" },
  this_year: { ru: "Год", en: "Year" },
  recent: { ru: "Последние операции", en: "Recent activity" },
  by_category: { ru: "По категориям", en: "By category" },
  trend: { ru: "Динамика", en: "Trend" },
  see_all: { ru: "Все", en: "See all" },
  back: { ru: "Назад", en: "Back" },
  no_ops: { ru: "Пока нет операций", en: "No activity yet" },
  add_first: { ru: "Отправьте трату в чат боту — она появится здесь.",
    en: "Send an expense to the bot — it appears here." },

  // history
  history: { ru: "История", en: "History" },
  search: { ru: "Поиск", en: "Search" },
  all: { ru: "Все", en: "All" },
  edit: { ru: "Изменить", en: "Edit" },
  delete: { ru: "Удалить", en: "Delete" },
  save: { ru: "Сохранить", en: "Save" },
  cancel: { ru: "Отмена", en: "Cancel" },
  title: { ru: "Описание", en: "Title" },
  amount: { ru: "Сумма", en: "Amount" },
  category: { ru: "Категория", en: "Category" },
  date: { ru: "Дата", en: "Date" },

  // budgets
  budgets: { ru: "Бюджеты", en: "Budgets" },
  budgets_hint: { ru: "Лимит на категорию в этом месяце", en: "Monthly limit per category" },
  set_limit: { ru: "Задать лимит", en: "Set limit" },
  limit: { ru: "Лимит", en: "Limit" },
  over_budget: { ru: "Перерасход", en: "Over budget" },
  left: { ru: "осталось", en: "left" },
  of: { ru: "из", en: "of" },

  // habits
  habits: { ru: "Отказ от вредных платежей", en: "Cut harmful spending" },
  habits_short: { ru: "Отказы", en: "Cutbacks" },
  habits_hint: { ru: "Откажитесь от вредной траты и считайте, сколько сэкономили.",
    en: "Drop a harmful expense and watch the savings grow." },
  new_habit: { ru: "Новый отказ", en: "New cutback" },
  habit_name: { ru: "От чего отказываемся", en: "What to cut" },
  daily_cost: { ru: "Стоимость в день", en: "Cost per day" },
  days_clean: { ru: "дней держусь", en: "days clean" },
  saved: { ru: "Сэкономлено", en: "Saved" },
  best: { ru: "Рекорд", en: "Best" },
  relapse: { ru: "Сорвался", en: "I slipped" },
  share_result: { ru: "Поделиться", en: "Share" },
  start: { ru: "Начать", en: "Start" },

  // subscriptions
  subscriptions: { ru: "Подписки", en: "Subscriptions" },
  subs_calendar: { ru: "Календарь списаний", en: "Charge calendar" },
  next_charge: { ru: "Следующее списание", en: "Next charge" },
  suggestions: { ru: "Похоже на подписки", en: "Looks recurring" },
  add_sub: { ru: "Добавить подписку", en: "Add subscription" },
  add: { ru: "Добавить", en: "Add" },
  per_month: { ru: "в месяц", en: "per month" },
  monthly: { ru: "Ежемесячно", en: "Monthly" },
  weekly: { ru: "Еженедельно", en: "Weekly" },
  yearly: { ru: "Ежегодно", en: "Yearly" },

  // insights
  insights: { ru: "Инсайты", en: "Insights" },
  vs_last_month: { ru: "к прошлому месяцу", en: "vs last month" },
  forecast: { ru: "Прогноз до конца месяца", en: "Forecast to month end" },
  forecast_note: { ru: "По текущему темпу трат", en: "At your current pace" },

  // rates
  rates: { ru: "Курсы", en: "Rates" },
  market: { ru: "Рынок", en: "Market" },
  converter: { ru: "Конвертер", en: "Converter" },
  amount_label: { ru: "Сумма", en: "Amount" },
  from: { ru: "Из", en: "From" },
  to: { ru: "В", en: "To" },
  result: { ru: "Результат", en: "Result" },
  rate_live: { ru: "Реальные данные", en: "Live data" },

  // achievements
  achievements: { ru: "Достижения", en: "Achievements" },
  unlocked: { ru: "Получено", en: "Unlocked" },
  locked: { ru: "В процессе", en: "In progress" },
  progress: { ru: "Прогресс", en: "Progress" },

  // goals
  goals: { ru: "Цели накоплений", en: "Savings goals" },
  goals_short: { ru: "Цели", en: "Goals" },
  new_goal: { ru: "Новая цель", en: "New goal" },
  goal_name: { ru: "Название цели", en: "Goal name" },
  target: { ru: "Цель", en: "Target" },
  top_up: { ru: "Пополнить", en: "Top up" },
  achieved: { ru: "Достигнуто", en: "Achieved" },

  // stash
  stash: { ru: "Заначка", en: "Round-up stash" },
  stash_hint: { ru: "Округляем траты и незаметно копим разницу.",
    en: "We round expenses up and quietly stash the change." },
  round_to: { ru: "Округлять до", en: "Round up to" },
  withdraw: { ru: "Забрать", en: "Withdraw" },
  enabled: { ru: "Включено", en: "Enabled" },

  // family
  family: { ru: "Совместный бюджет", en: "Shared budget" },
  family_short: { ru: "Семья", en: "Shared" },
  family_hint: { ru: "Ведите бюджет вместе с близкими. Чтобы вести вместе — пригласите.",
    en: "Run a budget together. To share, invite someone." },
  create_family: { ru: "Создать общий бюджет", en: "Create shared budget" },
  family_name: { ru: "Название бюджета", en: "Budget name" },
  invite: { ru: "Пригласить по ссылке", en: "Invite by link" },
  members: { ru: "Участники", en: "Members" },
  join: { ru: "Присоединиться", en: "Join" },
  invite_code: { ru: "Код приглашения", en: "Invite code" },

  // settings
  settings: { ru: "Настройки", en: "Settings" },
  language: { ru: "Язык", en: "Language" },
  base_currency: { ru: "Базовая валюта", en: "Base currency" },
  theme: { ru: "Тема", en: "Theme" },
  light: { ru: "Светлая", en: "Light" },
  premium: { ru: "Premium", en: "Premium" },
  premium_active: { ru: "Premium активен", en: "Premium active" },
  go_premium: { ru: "Оформить Premium", en: "Get Premium" },
  manage_categories: { ru: "Категории", en: "Categories" },
  export: { ru: "Экспорт в Excel", en: "Export to Excel" },
  referral: { ru: "Пригласить друга", en: "Invite a friend" },

  // common
  loading: { ru: "Загрузка", en: "Loading" },
  done: { ru: "Готово", en: "Done" },
  premium_required: { ru: "Доступно в Premium", en: "Available in Premium" },
  more: { ru: "Ещё", en: "More" },
};

let current: Lang = "en";
export function setLang(l: Lang) { current = l; }
export function getLang(): Lang { return current; }
export function t(key: string, fallback = ""): string {
  const e = DICT[key];
  if (!e) return fallback || key;
  return e[current] ?? e.en;
}
