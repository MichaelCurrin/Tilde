import {
  //   getAuthToken,
  setAuthToken,
  clearAuthToken,
} from "../utils/authTokenStorage";

import { fetchAndClean } from "./helpers";
import { API_BASE_URL } from "../config";

function calculateOffset({ page, limit }) {
  if (!page) throw new Error("page is empty");

  if (page < 1) throw new Error("page must be >= 1");
  return limit * (page - 1);
}

function objectToGetQueryString(obj) {
  var str = "";
  for (var key in obj) {
    if (str !== "") {
      str += "&";
    }
    str += key + "=" + encodeURIComponent(obj[key]);
  }
  return str;
}

async function whoAmI() {
  const url = `${API_BASE_URL}/api/who_am_i/`;
  const { response, responseData } = await fetchAndClean({ url });
  if (responseData.detail === "Invalid token.") clearAuthToken();
  return { response, responseData };
}

async function logout() {
  const url = `${API_BASE_URL}/api/logout/`;
  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
  });
  clearAuthToken();
  return { response, responseData };
}

async function authenticateWithOneTimeToken(data) {
  const url = `${API_BASE_URL}/social_auth/oauth_one_time_token_auth/`;

  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
    data,
  });
  setAuthToken({ value: responseData["token"], keep: true });

  return { response, responseData };
}

async function teamsPage({ page }) {
  const limit = 10;
  const offset = calculateOffset({ page, limit });
  const url = `${API_BASE_URL}/api/teams/?active=true&limit=${limit}&offset=${offset}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function teamEntity({ teamId }) {
  const url = `${API_BASE_URL}/api/teams/${teamId}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function userEntity({ userId }) {
  const url = `${API_BASE_URL}/api/users/${userId}/`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function recruitProjectsPage({ userId, page }) {
  const limit = 20;
  const offset = calculateOffset({ page, limit });

  const url = `${API_BASE_URL}/api/recruit_projects/?recruit_users=${userId}&limit=${limit}&offset=${offset}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function recruitProjectEntity({ projectId }) {
  if (!projectId) throw new Error("projectId is empty");
  const url = `${API_BASE_URL}/api/recruit_projects/${projectId}/`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function topicProgressEntity({ topicProgressId }) {
  const url = `${API_BASE_URL}/api/topic_progress/${topicProgressId}/`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function recruitProjectReviewsPage({
  projectId,
  page,
  reviewerUser,
  recruitUsers,
}) {
  const limit = 20;
  const offset = calculateOffset({ page, limit });

  let params = {
    limit,
    offset,
  };
  if (reviewerUser) params["reviewer_user"] = reviewerUser;
  if (recruitUsers) params["recruit_project__recruit_users"] = recruitUsers;
  if (projectId) params["recruit_project"] = projectId;
  // reviewer_user
  // recruit_project__recruit_users
  //   if (!projectId) throw new Error("projectId is empty");
  const getParams = objectToGetQueryString(params);
  const url = `${API_BASE_URL}/api/recruit_project_reviews/?${getParams}`;
  const { response, responseData } = await fetchAndClean({
    url,
  });
  return { response, responseData };
}

async function topicProgressReviewsPage({ topicProgressId, page }) {
  const limit = 20;

  const offset = calculateOffset({ page, limit });

  const url = `${API_BASE_URL}/api/topic_reviews/?topic_progress=${topicProgressId}&limit=${limit}&offset=${offset}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function userActionsCardsCompletedPage({ assigneeUserId, page }) {
  const limit = 20;

  const offset = calculateOffset({ page, limit });

  let url = `${API_BASE_URL}/api/card_summaries/?limit=${limit}&offset=${offset}&assignees=${assigneeUserId}&content_item__content_type=&ordering=-recruit_project__complete_time&status=C`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

// async function userActionsCardsStarted({
//     assigneeUserId,
//     page,
// }){
//     let url = `${API_BASE_URL}/api/card_summaries/?limit=${limit}&offset=${offset}&assignees=${assigneeUserId}&content_item__content_type=&ordering=-recruit_project__start_time&status=C`;
//   const { response, responseData } = await fetchAndClean({ url });
//   return { response, responseData };
// }

async function personallyAssignedCardSummariesPage({ assigneeUserId, page }) {
  const limit = 20;

  const offset = calculateOffset({ page, limit });

  let url = `${API_BASE_URL}/api/card_summaries/?limit=${limit}&offset=${offset}&assignees=${assigneeUserId}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function personallyAssignedCardSummaryEntity({ cardId }) {
  let url = `${API_BASE_URL}/api/card_summaries/${cardId}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function personallyAssignedAgileCardsPage({
  assigneeUserId,
  reviewerUserId,
  page,
  status,
}) {
  const limit = 20;

  const offset = calculateOffset({ page, limit });

  let url = `${API_BASE_URL}/api/agile_card/?status=${status}&limit=${limit}&offset=${offset}`;
  if (assigneeUserId) url += `&assignees=${assigneeUserId}`;
  if (reviewerUserId) url += `&reviewers=${reviewerUserId}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function agileCardEntity({ cardId }) {
  let url = `${API_BASE_URL}/api/agile_card/${cardId}/`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function cohortsPage({ page }) {
  const limit = 20;

  const offset = calculateOffset({ page, limit });

  const url = `${API_BASE_URL}/api/cohorts/?active=true&limit=${limit}&offset=${offset}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function cohortRecruits({ page, cohort }) {
  const limit = 20;

  const offset = calculateOffset({ page, limit });

  const url = `${API_BASE_URL}/api/recruit_cohorts/?limit=${limit}&offset=${offset}&cohort=${cohort}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function repositoryEntity({ repositoryId }) {
  const url = `${API_BASE_URL}/api/repository/${repositoryId}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}
async function repositoryCommitsPage({ repositoryId, page }) {
  const limit = 20;
  const offset = calculateOffset({ page, limit });

  const url = `${API_BASE_URL}/api/commit/?limit=${limit}&offset=${offset}&repository=${repositoryId}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}
async function repositoryPullRequestsPage({ repositoryId, page }) {
  const limit = 20;
  const offset = calculateOffset({ page, limit });
  const url = `${API_BASE_URL}/api/pull_request/?limit=${limit}&offset=${offset}&repository=${repositoryId}`;
  const { response, responseData } = await fetchAndClean({ url });
  return { response, responseData };
}

async function startProject({ cardId }) {
  const url = `${API_BASE_URL}/api/agile_card/${cardId}/start_project/`;
  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
  });
  return { response, responseData };
}
async function requestReview({ cardId }) {
  const url = `${API_BASE_URL}/api/agile_card/${cardId}/request_review/`;
  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
  });
  return { response, responseData };
}
async function cancelReviewRequest({ cardId }) {
  const url = `${API_BASE_URL}/api/agile_card/${cardId}/cancel_review_request/`;
  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
  });
  return { response, responseData };
}
async function addReview({ cardId, status, comments }) {
  const url = `${API_BASE_URL}/api/agile_card/${cardId}/add_review/`;
  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
    data: { status, comments },
  });
  return { response, responseData };
}

async function startTopic({ cardId }) {
  const url = `${API_BASE_URL}/api/agile_card/${cardId}/start_topic/`;
  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
  });
  return { response, responseData };
}
async function stopTopic({ cardId }) {
  const url = `${API_BASE_URL}/api/agile_card/${cardId}/stop_topic/`;
  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
  });
  return { response, responseData };
}
async function finishTopic({ cardId }) {
  const url = `${API_BASE_URL}/api/agile_card/${cardId}/finish_topic/`;
  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
  });
  return { response, responseData };
}
async function markWorkshopAttendance({ cardId, timestamp }) {
  const url = `${API_BASE_URL}/api/agile_card/${cardId}/mark_workshop_attendance/`;
  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
    data: { timestamp },
  });
  return { response, responseData };
}
async function cancelWorkshopAttendance({ cardId }) {
  const url = `${API_BASE_URL}/api/agile_card/${cardId}/cancel_workshop_attendance/`;
  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
  });
  return { response, responseData };
}

async function setProjectLinkSubmission({ cardId, linkSubmission }) {
  const url = `${API_BASE_URL}/api/agile_card/${cardId}/set_project_link/`;
  const { response, responseData } = await fetchAndClean({
    url,
    method: "POST",
    data: {
      linkSubmission,
    },
  });
  return { response, responseData };
}

export default {
  // TODO: get rid of this. Rather just export the functions individually
  everyone: {
    whoAmI,
    logout,
    authenticateWithOneTimeToken,
    teamsPage,
    teamEntity,
    userEntity,
  },

  recruits: {
    recruitProjectsPage,
    personallyAssignedAgileCardsPage,

    recruitProjectEntity,
    topicProgressEntity,
    recruitProjectReviewsPage,
    topicProgressReviewsPage,

    repositoryEntity,
    repositoryCommitsPage,
    repositoryPullRequestsPage,

    startProject,
    requestReview,
    cancelReviewRequest,
    addReview,

    startTopic,
    stopTopic,
    finishTopic,

    setProjectLinkSubmission,
    userActionsCardsCompletedPage,
  },
  staff: {
    cohortsPage,
    cohortRecruits,
    markWorkshopAttendance,
    cancelWorkshopAttendance,

    personallyAssignedCardSummariesPage,
    personallyAssignedCardSummaryEntity,
    agileCardEntity,
  },
};
