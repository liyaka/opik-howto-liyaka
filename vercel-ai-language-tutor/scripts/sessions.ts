// Two scripted learner sessions; each becomes one Opik thread. The learner makes
// mistakes on purpose so the judge has something to grade.
export const sessions = [
  {
    title: "Cafe: a mistake, a translation, a quiz",
    lessonId: "cafe-ordering",
    turns: [
      "Yo quiero un cortado sin azucar por favor, y yo necesito la cuenta ahora.",
      "How do I say 'to take away' politely when I order?",
      "Can you quiz me on the cafe vocabulary?",
    ],
  },
  {
    title: "Weekend: a preterite slip, then plans",
    lessonId: "weekend-plans",
    turns: [
      "El fin de semana pasado yo vaya a la playa con mis primos.",
      "Translate: 'I am going to visit my cousins next weekend'.",
      "Give me a three-question quiz on ir.",
    ],
  },
];
