"use client";

import {
  CalendarDays,
  ChartNoAxesCombined,
  Compass,
  History,
  House,
  Menu,
  Repeat2,
  Settings,
  Sparkles,
  UserRound,
  Users,
  X,
  Zap,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState, type ReactNode, type RefObject } from "react";

import { useTeam } from "@/app/providers/TeamProvider";
import { DeadlineCountdown } from "@/components/shell/DeadlineCountdown";


type Destination = {
  href: string;
  label: string;
  icon: LucideIcon;
};


const desktopDestinations: Destination[] = [
  { href: "/", label: "Overview", icon: House },
  { href: "/team", label: "My Team", icon: Users },
  { href: "/plan#transfer-center", label: "Transfer Center", icon: Repeat2 },
  { href: "/plan#ai-recommendations", label: "AI Recommendations", icon: Sparkles },
  { href: "/explore#player-market", label: "Players", icon: UserRound },
  { href: "/explore#fixture-matrix", label: "Fixtures", icon: CalendarDays },
  { href: "/plan#chip-advisor", label: "Chips", icon: Zap },
  { href: "/review#statistics", label: "Statistics", icon: ChartNoAxesCombined },
  { href: "/review", label: "Team History", icon: History },
  { href: "/settings", label: "Settings", icon: Settings },
];

const mobileDestinations: Destination[] = [
  { href: "/", label: "Overview", icon: House },
  { href: "/team", label: "My Team", icon: Users },
  { href: "/plan", label: "Plan", icon: Sparkles },
  { href: "/explore", label: "Explore", icon: Compass },
];


function Navigation({
  mobile = false,
  moreButtonRef,
  moreOpen = false,
  onMore,
}: {
  mobile?: boolean;
  moreButtonRef?: RefObject<HTMLButtonElement | null>;
  moreOpen?: boolean;
  onMore?: () => void;
}) {
  const pathname = usePathname();
  const destinations = mobile ? mobileDestinations : desktopDestinations;
  return (
    <nav className={mobile ? "saas-mobile-nav" : "saas-nav"} aria-label={mobile ? "Mobile primary" : "Primary"}>
      {destinations.map(({ href, label, icon: Icon }) => {
        const active = pathname === href.split("#", 1)[0];
        return (
          <Link key={href} href={href} className="saas-nav-link" aria-current={active ? "page" : undefined}>
            <Icon aria-hidden="true" size={18} />
            <span>{label}</span>
          </Link>
        );
      })}
      {mobile ? <button ref={moreButtonRef} type="button" className="saas-nav-link saas-mobile-more-trigger" aria-expanded={moreOpen} aria-controls="mobile-more-sheet" onClick={onMore}>
        <Menu aria-hidden="true" size={18} />
        <span>More</span>
      </button> : null}
    </nav>
  );
}


export function AppShell({ children }: { children: ReactNode }) {
  const { dashboard, teamId } = useTeam();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const moreButtonRef = useRef<HTMLButtonElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const mobileSheetRef = useRef<HTMLElement>(null);
  const closeMobileMenu = useCallback(() => {
    setMobileMenuOpen(false);
    queueMicrotask(() => moreButtonRef.current?.focus());
  }, []);
  const event = dashboard?.meta.event;
  const officialFetchedAt = dashboard?.meta.official?.fetched_at;
  const stale = dashboard?.meta.stale ?? dashboard?.meta.official?.stale ?? false;
  const liveMode = dashboard?.data.live?.status === "LIVE" && dashboard.data.live.finished !== true;
  const sourceLabel = !dashboard ? "Setup" : stale ? "Cached" : liveMode ? "Live" : "Official";
  const sourceClass = !dashboard ? "source-neutral" : stale ? "source-derived" : liveMode ? "source-live" : "source-official";
  const dataStatus = !dashboard ? "Connect your team" : stale ? "Cached FPL data" : liveMode ? "Live data ready" : "Official FPL ready";
  const freshness = officialFetchedAt
    ? `${stale ? "Cached" : "Updated"} ${new Date(officialFetchedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
    : "Team not connected";

  useEffect(() => {
    if (!mobileMenuOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    let active = true;
    queueMicrotask(() => {
      if (active) closeButtonRef.current?.focus();
    });
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeMobileMenu();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = Array.from(
        mobileSheetRef.current?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])') ?? [],
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      active = false;
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [closeMobileMenu, mobileMenuOpen]);

  return (
    <div className="saas-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <aside className="saas-sidebar">
        <Link href="/" className="saas-brand" aria-label="FPL AI overview">
          <span className="saas-brand-mark"><Sparkles size={18} aria-hidden="true" /></span>
          <span>FPL AI<small>Decision intelligence</small></span>
        </Link>
        <Navigation />
        <div className="saas-side-status">
          <span className={dashboard && !stale ? "status-dot status-online" : "status-dot"} />
          <div><strong>{dataStatus}</strong><small>{teamId ? `Team ${teamId}` : "Public Team ID"}</small></div>
        </div>
      </aside>

      <div className="saas-stage">
        <header className="saas-topbar">
          <div><span className={`source-pill ${sourceClass}`}>{sourceLabel}</span><strong>{event ? `Gameweek ${event}` : "FPL season"}</strong></div>
          <DeadlineCountdown deadline={dashboard?.meta.target_deadline_time ?? dashboard?.data.live?.next_deadline_time} event={dashboard?.meta.prediction_event ?? dashboard?.data.live?.next_event} />
          <span className="saas-freshness">{freshness}</span>
        </header>
        {dashboard?.meta.degraded ? (
          <div className="degraded-banner" role="status">
            {stale ? "Official FPL is temporarily unavailable. Showing the last cached data." : "Some analysis is unavailable. Official team data remains visible."}
          </div>
        ) : null}
        <main id="main-content" className="saas-content">{children}</main>
      </div>
      <Navigation mobile moreButtonRef={moreButtonRef} moreOpen={mobileMenuOpen} onMore={() => setMobileMenuOpen(true)} />
      {mobileMenuOpen ? <div className="mobile-more-backdrop" onMouseDown={(event) => { if (event.currentTarget === event.target) closeMobileMenu(); }}>
        <section id="mobile-more-sheet" className="mobile-more-sheet" role="dialog" aria-modal="true" aria-labelledby="mobile-more-title" ref={mobileSheetRef}>
          <header><div><span>Navigation</span><h2 id="mobile-more-title">More FPL AI tools</h2></div><button ref={closeButtonRef} type="button" aria-label="Close more tools" onClick={closeMobileMenu}><X size={18} aria-hidden="true" /></button></header>
          <p>Jump directly to the decision surface you need.</p>
          <nav aria-label="More destinations">
            {desktopDestinations.slice(2).map(({ href, label, icon: Icon }) => <Link key={href} href={href} onClick={closeMobileMenu}><Icon size={17} aria-hidden="true" /><span>{label}</span></Link>)}
          </nav>
        </section>
      </div> : null}
    </div>
  );
}
