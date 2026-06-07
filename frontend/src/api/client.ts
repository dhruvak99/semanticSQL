import { env } from '../config/env';

type RequestOptions = {
  signal?: AbortSignal;
};

export async function apiGet<TResponse>(path: string, options: RequestOptions = {}): Promise<TResponse> {
  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json'
    },
    signal: options.signal
  });

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return response.json() as Promise<TResponse>;
}

export async function apiPost<TRequest, TResponse>(
  path: string,
  body: TRequest,
  options: RequestOptions = {}
): Promise<TResponse> {
  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body),
    signal: options.signal
  });

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return response.json() as Promise<TResponse>;
}
