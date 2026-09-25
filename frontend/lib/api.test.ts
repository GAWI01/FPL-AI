import { afterEach, expect, test, vi } from "vitest";

import { API_BASE_URL, ApiError, fetchDashboard, fetchFixtureMatrix, fetchPlayers, fetchReview } from "./api";


afterEach(() => {
  vi.restoreAllMocks();
});


test("defaults to a deployment-safe same-origin API instead of localhost", () => {
  expect(API_BASE_URL).toBe("");
});


test("rejects a non-numeric team id before fetching", async () => {
  const fetchSpy = vi.spyOn(globalThis, "fetch");

  await expect(fetchDashboard("abc")).rejects.toThrow("numeric FPL Team ID");
  expect(fetchSpy).not.toHaveBeenCalled();
});


test("surfaces the backend detail for a failed dashboard request", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ detail: "FPL team was not found" }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    }),
  );

  await expect(fetchDashboard("123")).rejects.toEqual(
    new ApiError(502, "FPL team was not found"),
  );
});


test("rejects a malformed successful dashboard contract", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ data: { team: { team_id: "wrong" } }, meta: {}, errors: [] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );

  await expect(fetchDashboard("123")).rejects.toThrow("invalid dashboard contract");
});


test("fetches the latest finished review with the normalized team id", async () => {
  const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ data: { available: false }, meta: {}, errors: [] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );

  await fetchReview(" 123 ");

  expect(fetchSpy).toHaveBeenCalledWith(
    "/api/v1/review/123",
    expect.objectContaining({ cache: "no-store" }),
  );
});


test("adds an explicit gameweek when requesting a historical review", async () => {
  const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ data: { available: false }, meta: {}, errors: [] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );

  await fetchReview("123", 2);

  expect(fetchSpy.mock.calls[0][0]).toBe(
    "/api/v1/review/123?event=2",
  );
});


test("fetches the five-gameweek all-club fixture matrix", async () => {
  const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ data: { teams: [] }, meta: {}, errors: [] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );

  await fetchFixtureMatrix(5);

  expect(fetchSpy).toHaveBeenCalledWith(
    "/api/v1/fixture-matrix?horizon=5",
    expect.objectContaining({ cache: "no-store" }),
  );
});


test("fetches the public player market without a connected manager", async () => {
  const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ data: { players: [] }, meta: {}, errors: [] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );

  await fetchPlayers(50);

  expect(fetchSpy).toHaveBeenCalledWith(
    "/api/v1/players?limit=50",
    expect.objectContaining({ cache: "no-store" }),
  );
});
