import { useEffect, useState } from "react";
import { Shell } from "./components/Shell";
import { display } from "./lib/mockData";
import type { RouteKey } from "./lib/types";
import { Connect } from "./pages/Connect";
import { Home } from "./pages/Home";
import { SimplePage } from "./pages/SimplePages";

const routes: RouteKey[] = [
  "home",
  "connect",
  "photos",
  "dashboards",
  "devices",
  "home-assistant",
  "settings",
  "updates",
  "diagnostics"
];

function routeFromHash(): RouteKey {
  const hash = window.location.hash.replace(/^#\/?/, "");
  return routes.includes(hash as RouteKey) ? (hash as RouteKey) : "home";
}

export function App() {
  const [route, setRouteState] = useState<RouteKey>(routeFromHash);
  const [health, setHealth] = useState<"loading" | "ok" | "offline">("loading");

  const setRoute = (nextRoute: RouteKey) => {
    window.location.hash = nextRoute;
    setRouteState(nextRoute);
  };

  useEffect(() => {
    fetch("/api/health")
      .then((response) => setHealth(response.ok ? "ok" : "offline"))
      .catch(() => setHealth("offline"));
  }, []);

  useEffect(() => {
    const onHashChange = () => setRouteState(routeFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  return (
    <Shell activeRoute={route} onNavigate={setRoute}>
      <div className="top-strip">
        <span className={`status-dot ${health === "ok" ? "good" : health === "loading" ? "neutral" : "danger"}`} />
        <span>Hub API: {health}</span>
      </div>
      {route === "home" && <Home display={display} onConnect={() => setRoute("connect")} />}
      {route === "connect" && <Connect />}
      {route !== "home" && route !== "connect" && <SimplePage route={route} />}
    </Shell>
  );
}
