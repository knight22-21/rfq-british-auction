import type {
  BidResult,
  QuoteCreateInput,
  RfqCreateInput,
  RfqDetail,
  RfqSummary,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

interface Envelope<T> {
  success: boolean;
  data: T;
  serverTime: string;
  error?: { code: string; message: string };
}

export interface ApiResult<T> {
  data: T;
  serverTime: string;
}

export class ApiRequestError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  let body: Envelope<T> | null = null;
  try {
    body = (await response.json()) as Envelope<T>;
  } catch {
    body = null;
  }

  if (!response.ok || !body?.success) {
    throw new ApiRequestError(
      body?.error?.code ?? "REQUEST_FAILED",
      body?.error?.message ?? `Request failed with status ${response.status}.`,
    );
  }

  return { data: body.data, serverTime: body.serverTime };
}

export const api = {
  listRfqs: () => request<RfqSummary[]>("/api/rfqs"),
  getRfq: (id: string) => request<RfqDetail>(`/api/rfqs/${id}`),
  createRfq: (payload: RfqCreateInput) =>
    request<RfqSummary>("/api/rfqs", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  submitQuote: (id: string, payload: QuoteCreateInput) =>
    request<BidResult>(`/api/rfqs/${id}/quotes`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
