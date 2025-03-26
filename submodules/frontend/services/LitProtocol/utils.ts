import { WebUploader } from "@irys/web-upload";
import { WebEthereum } from "@irys/web-upload-ethereum";
import { EthersV6Adapter } from "@irys/web-upload-ethereum-ethers-v6";
import { ethers } from "ethers";
import { LitNodeClient } from "@lit-protocol/lit-node-client";
import { LIT_NETWORK } from "@lit-protocol/constants";
import { SecretsManager } from "@aws-sdk/client-secrets-manager";

// Hardcoded secret name for Lit Protocol secrets
const LIT_PROTOCOL_SECRET_NAME = "LitProtocolPaymentDelegationSecrets";

// Global initialization status
let isInitialized = false;
let initializationPromise: Promise<void> | null = null;

// Global credentials
let LIT_RELAYER_API_KEY: string;
let LIT_PAYER_SECRET_KEY: string;

// Choose network based on environment
export const getLitNetwork = () => {
  return process.env.NODE_ENV === "production"
    ? LIT_NETWORK.Datil
    : LIT_NETWORK.DatilDev;
};

// Initialize the Lit client
export const litClient = new LitNodeClient({
  litNetwork: getLitNetwork(),
});

// Get secrets from AWS Secrets Manager
export const getSecrets = async () => {
  console.log("[LIT] Getting secrets from AWS Secrets Manager");
  const secretsManager = new SecretsManager({
    region: process.env.AWS_REGION || "us-west-1",
  });

  const response = await secretsManager.getSecretValue({
    SecretId: LIT_PROTOCOL_SECRET_NAME,
  });

  const secrets = JSON.parse(response.SecretString || "{}");

  if (!secrets.LIT_RELAYER_API_KEY) {
    console.error("[LIT] ERROR: LIT_RELAYER_API_KEY is missing in secrets");
  }

  if (!secrets.LIT_PAYER_SECRET_KEY) {
    console.warn(
      "[LIT] WARNING: LIT_PAYER_SECRET_KEY is missing - may need to register"
    );
  }

  return {
    LIT_RELAYER_API_KEY: secrets.LIT_RELAYER_API_KEY,
    LIT_PAYER_SECRET_KEY: secrets.LIT_PAYER_SECRET_KEY,
  };
};

// Get the appropriate relayer URL based on network
export const getRelayerUrl = (endpoint: string) => {
  const network =
    process.env.NODE_ENV === "production" ? "datil" : "datil-test";
  return `https://${network}-relayer.getlit.dev/${endpoint}`;
};

export const gatewayAddress = "https://gateway.irys.xyz/";

export const getIrysUploader = async () => {
  const provider = new ethers.BrowserProvider(window.ethereum);
  const irysUploader = await WebUploader(WebEthereum).withAdapter(
    EthersV6Adapter(provider)
  );
  return irysUploader;
};

export const getAccessControlConditions = () => {
  return [
    {
      conditionType: "evmBasic" as const,
      contractAddress: "" as const,
      standardContractType: "" as const,
      chain: "ethereum" as const,
      method: "eth_getBalance" as const,
      parameters: [":userAddress", "latest"],
      returnValueTest: {
        comparator: ">=" as const,
        value: "10000000000000", // 0.00001 ETH
      },
    },
  ];
};

// Master initialization function - all operations must wait for this
export const initializeLitProtocol = async (): Promise<void> => {
  // If already initialized, return immediately
  if (isInitialized) {
    return;
  }

  // If initialization is in progress, wait for it to complete
  if (initializationPromise) {
    return initializationPromise;
  }

  // Start initialization
  console.log("[LIT] Starting initialization");

  initializationPromise = (async () => {
    try {
      // Step 1: Connect to Lit network
      console.log("[LIT] Connecting to Lit Network");
      await litClient.connect();
      console.log("[LIT] Lit client connected successfully");

      // Step 2: Load secrets
      console.log("[LIT] Loading secrets");
      const secrets = await getSecrets();
      LIT_RELAYER_API_KEY = secrets.LIT_RELAYER_API_KEY;
      LIT_PAYER_SECRET_KEY = secrets.LIT_PAYER_SECRET_KEY;

      // Verify we have the API key
      if (!LIT_RELAYER_API_KEY) {
        throw new Error("LIT_RELAYER_API_KEY not found in secrets");
      }

      // Mark as initialized
      isInitialized = true;
      console.log("[LIT] Initialization complete");
    } catch (error) {
      console.error("[LIT] Initialization failed:", error);
      // Reset initialization state so it can be retried
      initializationPromise = null;
      throw error;
    }
  })();

  return initializationPromise;
};

/**
 * Register a new payer wallet with the Payment Delegation Database
 */
export const registerPayer = async (): Promise<{
  payerWalletAddress: string;
  payerSecretKey: string;
}> => {
  await initializeLitProtocol();

  const headers = {
    "api-key": LIT_RELAYER_API_KEY,
    "Content-Type": "application/json",
  };

  console.log("[LIT] Registering new payer");

  try {
    const url = getRelayerUrl("register-payer");
    const response = await fetch(url, {
      method: "POST",
      headers: headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(
        `[LIT] Register payer failed: ${response.status} - ${errorText}`
      );
      throw new Error(`Error: ${errorText}`);
    }

    const data = await response.json();
    console.log(`[LIT] New payer registered: ${data.payerWalletAddress}`);

    // Update the global variable
    LIT_PAYER_SECRET_KEY = data.payerSecretKey;

    return {
      payerWalletAddress: data.payerWalletAddress,
      payerSecretKey: data.payerSecretKey,
    };
  } catch (error) {
    console.error("[LIT] Error registering payer:", error);
    throw error;
  }
};

/**
 * Add users as payees for the payer wallet
 */
export const addUsers = async (users: string[]): Promise<boolean> => {
  await initializeLitProtocol();

  // Verify we have the required credentials
  if (!LIT_RELAYER_API_KEY || !LIT_PAYER_SECRET_KEY) {
    console.error("[LIT] Missing API key or payer secret key");
    throw new Error("API key or payer secret key is missing");
  }

  const headers = {
    "api-key": LIT_RELAYER_API_KEY,
    "payer-secret-key": LIT_PAYER_SECRET_KEY,
    "Content-Type": "application/json",
  };

  console.log(`[LIT] Adding ${users.length} users as delegatees`);

  try {
    const url = getRelayerUrl("add-users");
    const response = await fetch(url, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(users),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(
        `[LIT] Add users failed: ${response.status} - ${errorText}`
      );
      throw new Error(`Error: ${errorText}`);
    }

    const data = await response.json();
    if (data.success !== true) {
      throw new Error(`Error: ${data.error}`);
    }
    console.log("[LIT] Added users as delegatees successfully");

    return true;
  } catch (error) {
    console.error("[LIT] Error adding users:", error);
    throw error;
  }
};

/**
 * Adds the current user to the Payment Delegation Database
 */
export const addCurrentUserAsDelegatee = async (): Promise<boolean> => {
  await initializeLitProtocol();

  try {
    // Get the user's address from browser ethereum provider
    const provider = new ethers.BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();
    const userWalletAddress = await signer.getAddress();

    console.log(
      `[LIT] Adding current user (${userWalletAddress}) to payment delegation database`
    );

    return await addUsers([userWalletAddress]);
  } catch (error) {
    console.error("[LIT] Error adding current user as delegatee:", error);
    throw error;
  }
};

// Make sure a specific wallet address is registered in the payment delegation system
export const ensureUserIsRegistered = async (
  address: string
): Promise<boolean> => {
  try {
    await initializeLitProtocol();

    // If we don't have a payer secret key, we need to register a new payer
    if (!LIT_PAYER_SECRET_KEY) {
      console.log("[LIT] No payer secret key found, registering new payer");
      const { payerSecretKey } = await registerPayer();
      LIT_PAYER_SECRET_KEY = payerSecretKey;
      console.log("[LIT] New payer registered successfully");
    }

    // Add the user to the payment delegation database
    return await addUsers([address]);
  } catch (error) {
    console.error("[LIT] Error ensuring user is registered:", error);
    throw error;
  }
};

// Export credentials for other modules to use
export const getCredentials = () => {
  return {
    LIT_RELAYER_API_KEY,
    LIT_PAYER_SECRET_KEY,
  };
};
