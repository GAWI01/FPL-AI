"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { fetchDashboard } from "@/lib/api";
import type { DashboardEnvelope } from "@/lib/contracts";


const STORAGE_KEY = "fpl-ai-team-id";
const REFRESH_INTERVAL_MS = 60_000;


type TeamContextValue = {
  teamId: string | null;
  dashboard: DashboardEnvelope | null;
  loading: boolean;
  error: string | null;
  connect: (teamId: string) => Promise<void>;
  disconnect: () => void;
  refresh: () => Promise<void>;
};


const TeamContext = createContext<TeamContextValue | null>(null);


export function TeamProvider({ children }: { children: ReactNode }) {
  const [teamId, setTeamId] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DashboardEnvelope | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const load = useCallback(async (value: string, persist: boolean) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchDashboard(value, controller.signal);
      setTeamId(value);
      setDashboard(result);
      if (persist) localStorage.setItem(STORAGE_KEY, value);
    } catch (caught) {
      if (controller.signal.aborted) return;
      setError(caught instanceof Error ? caught.message : "Could not load FPL team");
      throw caught;
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, []);

  const connect = useCallback(async (value: string) => {
    const normalized = value.trim();
    await load(normalized, true);
  }, [load]);

  const refresh = useCallback(async () => {
    if (!teamId) return;
    try {
      await load(teamId, false);
    } catch {
      // The provider exposes the error while retaining the last good dashboard.
    }
  }, [load, teamId]);

  const disconnect = useCallback(() => {
    abortRef.current?.abort();
    localStorage.removeItem(STORAGE_KEY);
    setTeamId(null);
    setDashboard(null);
    setError(null);
    setLoading(false);
  }, []);

  useEffect(() => {
    let active = true;
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) queueMicrotask(() => {
      if (active) void load(saved, false).catch(() => undefined);
    });
    return () => {
      active = false;
      abortRef.current?.abort();
    };
  }, [load]);

  useEffect(() => {
    if (!teamId) return;
    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") void refresh();
    }, REFRESH_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, [refresh, teamId]);

  return (
    <TeamContext.Provider value={{
      teamId,
      dashboard,
      loading,
      error,
      connect,
      disconnect,
      refresh,
    }}>
      {children}
    </TeamContext.Provider>
  );
}


export function useTeam(): TeamContextValue {
  const context = useContext(TeamContext);
  if (!context) throw new Error("useTeam must be used within TeamProvider");
  return context;
}
