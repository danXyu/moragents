import { Axios } from "axios";

export const postTweet = async (
  backendClient: Axios,
  content: string
): Promise<void> => {
  const apiKey = localStorage.getItem("apiKey");
  const apiSecret = localStorage.getItem("apiSecret");
  const accessToken = localStorage.getItem("accessToken");
  const accessTokenSecret = localStorage.getItem("accessTokenSecret");
  const bearerToken = localStorage.getItem("bearerToken");

  if (
    !apiKey ||
    !apiSecret ||
    !accessToken ||
    !accessTokenSecret ||
    !bearerToken
  ) {
    throw new Error(
      "X API credentials not found. Please set them in the settings."
    );
  }

  try {
    await backendClient.post("/tweet/post", {
      post_content: content,
      api_key: apiKey,
      api_secret: apiSecret,
      access_token: accessToken,
      access_token_secret: accessTokenSecret,
      bearer_token: bearerToken,
    });
  } catch (error) {
    console.error("Error posting tweet:", error);
    throw error;
  }
};

export const regenerateTweet = async (
  backendClient: Axios
): Promise<string> => {
  try {
    const response = await backendClient.post("/tweet/regenerate");
    return response.data;
  } catch (error) {
    console.error("Error regenerating tweet:", error);
    throw error;
  }
};
