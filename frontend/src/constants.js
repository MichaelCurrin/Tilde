// TODO get all constants from the backend
// or generate constants file when we deploy?
export const BLOCKED = "B";
export const READY = "R";
export const IN_PROGRESS = "IP";
export const REVIEW_FEEDBACK = "RF";
export const IN_REVIEW = "IR";
export const COMPLETE = "C";

export const AGILE_CARD_STATUS_CHOICES = {
  [BLOCKED]: "Blocked",
  [READY]: "Ready",
  [IN_PROGRESS]: "In Progress",
  [REVIEW_FEEDBACK]: "Feedback",
  [IN_REVIEW]: "In Review",
  [COMPLETE]: "Complete",
};

export const INCORRECT = "i";
export const CORRECT = "c";
export const CONTRADICTED = "d";

export const REVIEW_VALIDATED_STATUS_CHOICES = {
  [INCORRECT]: "incorrect",
  [CORRECT]: "correct",
  [CONTRADICTED]: "contradicted",
};

export const AGILE_CARD_STATUS_CHOICES_SHOW_REVIEWER = [
  // if a user is the reviewer for a card, and the card is in one of these columns, then show it on the board
  IN_PROGRESS,
  REVIEW_FEEDBACK,
  IN_REVIEW,
];

export const AGILE_COLUMNS = {
  Backlog: [READY, BLOCKED],
  "In Progress": [IN_PROGRESS],
  "Review Feedback": [REVIEW_FEEDBACK],
  Review: [IN_REVIEW],
  Complete: [COMPLETE],
};

export const NOT_YET_COMPETENT = "NYC";
export const COMPETENT = "C";
export const EXCELLENT = "E";
export const RED_FLAG = "R";

export const REVIEW_STATUS_CHOICES = {
  [COMPETENT]: "competent",
  [RED_FLAG]: "red flag",
  [NOT_YET_COMPETENT]: "not yet competent",
  [EXCELLENT]: "excellent",
};

export const MANAGE_CARDS = "MANAGE_CARDS";
export const VIEW_ALL = "VIEW_ALL";
export const ASSIGN_REVIEWERS = "ASSIGN_REVIEWERS";
export const REVIEW_CARDS = "REVIEW_CARDS";
export const TRUSTED_REVIEWER = "TRUSTED_REVIEWER";

export const TEAM_PERMISSIONS = [
  MANAGE_CARDS,
  VIEW_ALL,
  ASSIGN_REVIEWERS,
  REVIEW_CARDS,
  TRUSTED_REVIEWER,
];

export default {
  AGILE_CARD_STATUS_CHOICES,
  AGILE_COLUMNS,
  REVIEW_STATUS_CHOICES,
  AGILE_CARD_STATUS_CHOICES_SHOW_REVIEWER,
  REVIEW_VALIDATED_STATUS_CHOICES,

  BLOCKED,
  READY,
  IN_PROGRESS,
  REVIEW_FEEDBACK,
  IN_REVIEW,
  COMPLETE,
};
