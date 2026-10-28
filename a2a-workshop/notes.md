# Agent2Agent (A2A) Workshop Notes

MCP Conference, A2A workshop, 2026-10-22

> Working notes. These get added to during the workshop and reorganized at the end.

## 1. What is A2A?

An open protocol that lets AI agents discover each other and work together, even when they were built by different vendors on different frameworks (LangGraph, CrewAI, Google ADK, …). Google announced it in April 2025 and later donated it to the Linux Foundation.

### A2A vs. MCP

| | MCP | A2A |
|---|---|---|
| Connects | Agent ↔ tools and data | Agent ↔ agent |
| The other side is | Passive (function, API, file) | Autonomous: reasons, asks questions, runs for a long time |
| Discovery | `tools/list` | Agent Card |

They work together: an agent uses MCP for its own tools and A2A to hand work off to other agents.

### How MCP and A2A line up (a common mix-up)

| MCP | A2A |
|---|---|
| MCP server | A2A agent (remote agent / A2A server) |
| Tools | Skills |
| `tools/list` response | Agent Card |

- ✅ An MCP server exposes a list of **tools**. An Agent Card describes **one agent** and lists its **skills**.
- ❌ It's *not* true that "an Agent Card wraps a list of agents." A list of agents is an **agent registry**, which the core spec doesn't define. Agents are found through a well-known URL, a curated registry, or direct configuration.
- **Tool vs. skill:** a tool is called like a function with exact arguments. A skill is a description: you send a message, and the agent decides how to do the work (and may ask follow-up questions).

### Which one to publish for other teams

| You built… | You want other teams to… | Publish it as |
|---|---|---|
| A set of **tools** | Let *their* agent call your tools directly | **MCP server** |
| An **agent** (own model, prompts, logic) | Hand the whole job to your agent | **A2A agent** + Agent Card |
| An API for regular code (not AI agents) | Call it from services or scripts | Plain REST / gRPC |

They combine: `Other team's agent ──A2A──► Your agent ──MCP──► your tools`

**Key question: who does the thinking?** With MCP, the caller's agent decides which tools to use. With A2A, *your* agent decides, and the caller only states what it wants.

### Whose compute gets used?

| Setup | Tool execution | LLM reasoning (tokens) |
|---|---|---|
| Remote MCP server (you host it over HTTP) | **Yours** | Caller's |
| Local MCP server (stdio, caller runs your package) | Caller's (but calls to your backend still hit you) | Caller's |
| A2A agent | **Yours** | **Yours** |

- Exception: MCP **sampling** lets a server ask the *client's* LLM to generate text, so the server borrows the caller's model.

#### MCP sampling in more detail

- **Direction flips:** the server sends `sampling/createMessage` to the client *during* a tool call; the client runs the prompt on its own LLM and returns the answer.
- **Why use it:** the server needs no LLM API key, has no LLM cost, and uses whatever model the caller already has.
- **Flow:** `tools/call` → server does its own work (its compute) → `sampling/createMessage` → client's LLM (caller's tokens) → result back → tool result.
- **Python SDK:** inside a tool, `await ctx.session.create_message(messages=[...], max_tokens=...)`.
- **The client stays in control:** it must declare sampling support (many clients don't support it yet), picks the model (the server only gives preferences for cost, speed or intelligence), and should let the user review the prompt and the answer.
- **Risk:** a server can put any prompt into the caller's model, which opens the door to prompt injection, so human review matters.
- **vs. A2A:** an A2A agent always reasons with its own LLM. An MCP server with sampling is still a tool that borrows reasoning from its caller.
- If you host a shared server: use **auth** to know who's calling, **rate limits and quotas** to cap usage, and **per-caller logging** to charge costs back.
- In the lab: the leaderboard's BigQuery lookup runs in the hosting project; your orchestrator only spends tokens deciding to call it.
- **Rule: whoever hosts the tool *and* the data it reads or writes pays for it.** Lab: `write_local_mcp_kb` → your own file; registering on the leaderboard → the host's BigQuery.
- **Writes are a responsibility, not just a cost:** another team's writes land in your store, so you own the storage, backups, data quality and cleanup.
  - Give out read access widely and write access narrowly (lab: writes need an extra `write_passcode`).
  - Make writes idempotent, because agents may retry the same call.

### Core concepts

- **Agent Card**: JSON at `/.well-known/agent-card.json` listing the agent's name, skills, endpoint, capabilities and auth
- **Client agent / remote agent**: the side that asks vs. the side that does the work
- **Task**: a stateful unit of work: `submitted → working → input-required → completed | failed | canceled`
- **Message**: one conversation turn, with role `user` or `agent`
- **Part**: content inside a message: `TextPart`, `FilePart`, `DataPart`
- **Artifact**: the output a task produces

### Request flow

1. Client fetches the Agent Card (discovery)
2. Client sends `message/send` (JSON-RPC 2.0 over HTTPS)
3. Remote agent sends progress updates over SSE, or push notifications to a webhook for long jobs
4. Task ends as `completed` with artifacts

## 2. Why do we need another protocol?

> Existing protocols like REST, gRPC and MQTT move bytes between servers, but they don't standardize how autonomous agents **discover skills, negotiate tasks, and collaborate**. Without A2A, every multi-agent system becomes a tangled web of brittle custom wrappers.

- A2A **runs on top of** HTTP, JSON-RPC and gRPC. It doesn't replace them. It adds an agreed meaning for what agents say.
- **N×M problem**: N agents with custom wrappers need about N² adapters. With a shared protocol, each agent implements it once (N total).
- What A2A standardizes that REST leaves to you:
  - Discovery → Agent Card
  - Job status → task lifecycle
  - Follow-up questions → `input-required` with multi-turn messages
  - Data formats → Parts
  - Long-running work → SSE streaming and push notifications
  - Auth → schemes declared on the card (OAuth2, OIDC, API keys)
- **Opacity is a feature**: agents show their skills, never their prompts, models or data.

### When you *don't* need A2A

- Everything runs in one process with one framework → use the framework's own message passing
- The callee is a deterministic tool → use MCP or a plain API
- One team owns every piece → the cost of a protocol may not be worth it

**Rule of thumb:** MCP when the other side is a *tool*, A2A when it's an *agent you don't control*, plain function calls when you control everything.

## 3. Hands-on lab: from local agent to multi-agent A2A orchestrator

Runs in Google Cloud Shell (Qwiklabs temporary project). Starter files are copied from `gs://${PROJECT_ID}-a2a-workshop/`. Python 3.13, `uv`, `google-adk[a2a]`.

### The four agents

| Agent | Role | Where |
|---|---|---|
| `my_awesome_analytics_agent` | **Your** orchestrator: BigQuery names analytics + local notes (`local_kb.json`) | Local (ADK) |
| `gateway_agent` | Registry and token broker: finds agents, issues `X-Gateway-Token` | Cloud Run |
| `corporate_names_analytics_agent` | Protected corporate directory; also issues the leaderboard `write_passcode` | Cloud Run, token required |
| `a2a_workshop_names_analytics` | Shared attendee leaderboard (BigQuery, read/write) | Cloud Run, token + passcode for writes |

### Task by task

| Task | What you do | Lesson |
|---|---|---|
| 2. Local tools only | Agent with 3 tools: `analyze_name_in_bigquery`, `query_local_mcp_kb`, `write_local_mcp_kb`. Asking about the corporate directory fails. | An agent is limited by what it can reach |
| 3. Hardcoded REST | Add two `httpx` wrappers for `GET /api/v1/lookup` and `POST /api/v1/token`. The exact key `corp_analytics_registry` works; the natural name `corporate_names_analytics_agent` → **400** | REST needs exact, stable names; renames and versions break callers |
| 4. Switch to A2A | Replace both wrappers with one `RemoteA2aAgent` (pointed at the gateway's Agent Card), wrapped in `AgentTool`. Add `contact_discovered_a2a_agent` to call agents found at runtime | Connect to one trusted agent, discover the rest at runtime |
| 5. Zero-trust auth | Calling without a token → **401**. With one: read client identity, get a token from the gateway, attach it as an HTTP header, then query succeeds | Finding an agent ≠ being allowed to use it |
| 6. Chain agents | Token + passcode from corporate agent → register your name on the leaderboard → get a `FLAG{A2A-LEADERBOARD-...}` | Agents can combine permissions from several agents (power *and* risk) |
| 7. (stretch) OpenAI Agents SDK | Same workflow from `task_7/openai_agent.py`; remote agents unchanged | A2A is framework-neutral |
| 8. (stretch) Be a server | `to_a2a(root_agent, port=8001)` + uvicorn; the OpenAI client calls *your* agent | Full task lifecycle: streaming, `input-required`, resume, `tasks/get` |

### Key code patterns (ADK)

```python
# Task 4: one declaration replaces per-endpoint REST client code
gateway_agent = RemoteA2aAgent(
    name="gateway_agent",
    description="Remote Gateway Agent for service discovery and token brokering.",
    agent_card=f"{GATEWAY_URL}{AGENT_CARD_WELL_KNOWN_PATH}",
)
tools=[..., AgentTool(agent=gateway_agent), contact_discovered_a2a_agent]

# Task 8: publish your own agent as an A2A server
from google.adk.a2a.utils.agent_to_a2a import to_a2a
a2a_app = to_a2a(root_agent, port=8001)
# run: uvicorn my_awesome_analytics_agent.agent:a2a_app --port 8001
```

- **`RemoteA2aAgent`** fetches the Agent Card once, reads the endpoint, and sends requests as JSON-RPC `message/send`.
- **`AgentTool(agent=...)` vs. `sub_agents=[...]`**: `AgentTool` calls the remote agent like a tool, and *your* agent stays in charge and gets the result back. A sub-agent *takes over* the conversation.
- **`to_a2a()`** auto-generates the Agent Card (skills come from your tools) and the JSON-RPC endpoint.

### What a caller needs to speak A2A (from Task 7)

1. `GET /.well-known/agent-card.json`
2. `POST` JSON-RPC 2.0 `message/send` (or `message/stream` for SSE)

Any framework that can do these two things can join (ADK, OpenAI Agents SDK, LangGraph, CrewAI).

### JSON-RPC methods seen in the lab

| Method | Used for |
|---|---|
| `message/send` | Synchronous request → response (Tasks 4–7) |
| `message/stream` | Same, but streams progress over SSE (Task 8) |
| `tasks/get` | Check a task's current state by `taskId` (Task 8) |

Task 8 lifecycle: `submitted → working → input-required` (asks for Y/n) `→` resume with the same `taskId` `→ completed`

### REST vs. A2A in the lab

| | REST (Task 3) | A2A (Task 4) |
|---|---|---|
| Self-description | Swagger `/docs`, written for human developers | Agent Card, written for agents |
| Client code | One hand-written wrapper per endpoint | One declaration per agent; the rest found at runtime |
| Name matching | Exact dictionary key, else 400 | Gateway's LLM maps the intent to the right entry |
| Caveat | Deterministic | Flexible but **not deterministic**; production adds exact IDs, policy, logging |

### Lab simplifications vs. production

| In the lab | In production |
|---|---|
| Custom `gateway_agent` as registry | Managed registry: ARD (Agentic Resource Discovery) or an enterprise AI Catalog |
| API key in `local_kb.json`, passed through the LLM's context | Workload or agent identity (e.g. a service account); secrets never reach the LLM |
| Auth described in prose | Declared in the Agent Card's `securitySchemes` |
| Plain Python functions as "local MCP" | Real MCP servers |
| — | Policy for which agent may call which; every call logged and traceable |

**Security takeaway:** chained agents can do together what none could do alone, so each agent must enforce its own access checks on every hop.

### How trust chains, and how identity should travel

**In the lab:** `api_key` → gateway issues `X-Gateway-Token` → corporate agent trusts the token, returns the passcode → leaderboard trusts the passcode, allows the write. Each agent trusts a credential that a *different* agent issued, and the orchestrator carries them along.

**What the lab does wrong on purpose:**
1. Secrets (API key, passcode) pass through the LLM's context.
2. The passcode is a shared secret: the leaderboard can't tell *who* is writing.
3. Only the *client* (`DEV-774`) is identified, never the human user.

**Confused deputy:** an agent uses its *own* broad service account for a user who has less access. Example: Alice asks an HR agent, and the salary agent sees only `HR-BOT`, so it returns everyone's salaries. The downstream agent must know **who is calling** (the agent) *and* **who it's calling for** (the user), and allow only what both may do.

**Production fix: delegated tokens** (OAuth 2.0 Token Exchange, RFC 8693):
- Signed by an identity provider → can't be forged
- Carry the **user + actor** → no confused deputy
- **Audience**: valid for one agent only → can't be replayed elsewhere
- **Scope narrows at each hop** → permissions can only shrink
- **Short-lived** (minutes)
- **Kept out of the LLM**: code or infrastructure attaches tokens as HTTP headers

**Answer:** don't expose *secrets*, but *do* pass *identity*, as a signed, scoped, short-lived token.
**Rule: keep secrets in code, keep decisions in the LLM.**

## Questions to ask practitioners

Ask for stories, not definitions: "Tell me about a time when…" or "What broke first?" Watch for whether the answer describes something they actually run or a plan.

### ⭐ Top 6 if you only have a few minutes

1. When a remote agent you call gets stuck or goes quiet, how do you notice, and what does your orchestrator do?
2. How do you budget and cap LLM and compute spend per agent? Who gets the bill when team A's agent calls team B's?
3. How do you trace one user request across five agents owned by three teams?
4. Is A2A actually in production at your company, or do most multi-agent systems still run in one process with one framework?
5. How does the *original user's* identity and permission travel through a chain of agents, so a downstream agent doesn't act with more access than the user has?
6. How do you test or evaluate an agent that depends on other teams' agents you don't control?

### 1. Compute, cost and quotas

- How do you set quotas: per calling agent, per team, per end user, or per task?
- What happens when a caller hits its quota: hard reject, queue, or drop to a cheaper model?
- Have you had a runaway loop, with two agents calling each other forever? How did you catch it, and what limit stops it now (max hops, max tokens per task, max depth)?
- For an A2A agent you expose, the caller pays nothing for *your* LLM reasoning. How do you charge back or price that?
- Do you cache results across callers, or is every request a fresh LLM run?

### 2. Reliability and failure handling ("what if a sub-agent gets stuck?")

- What timeout do you set on a task stuck in `working`? Does it differ for agents that are supposed to run long?
- Do you use `tasks/cancel`? Does the remote agent actually stop its work and its spending, or just stop replying?
- How do you tell "slow but making progress" from "stuck"? Do you rely on streaming heartbeats or progress events?
- Do you retry failed tasks? How do you keep a retry from doing a write twice?
- If a sub-agent returns something that *looks* right but is wrong, who catches it: the orchestrator, a validator agent, or a human?
- Does one bad agent ever take down the whole workflow? Do you use circuit breakers or fallback agents?
- What happens to a task in `input-required` when the human never answers?

### 3. Security and trust

- Do downstream agents see the *end user's* identity, the *calling agent's* identity, or both?
- How do you prevent the confused-deputy problem from lab Task 6, where agents chain permissions to do something no single agent was allowed to do?
- How do you defend against prompt injection carried in another agent's response?
- Which auth do you actually use between agents: OAuth2 client credentials, mTLS, workload identity, something else?
- Do agents get short-lived, narrowly scoped tokens per task, or long-lived ones?

### 4. Discovery, versioning and governance

- Who is allowed to publish an Agent Card to your registry, and who reviews it?
- How do you version an agent? What happens to callers when its skills or behavior change?
- The lab's gateway matched names with an LLM. Do you accept that non-determinism in production, or require exact IDs?
- How do you retire an agent that other teams depend on?
- Is there a policy layer deciding which agent may call which? Who owns it?

### 5. Observability and debugging

- What trace or correlation ID do you pass across agents? OpenTelemetry?
- When an end result is wrong, how do you find which agent in the chain caused it?
- What do you log from prompts and responses, given privacy rules?
- What dashboards does an agent's owner actually check day to day?

### 6. Testing and evaluation

- Do you mock remote agents in tests, or test against live ones?
- How do you run regression tests when the remote agent's model changes without you knowing?
- Do you have contract tests based on Agent Cards?

### 7. Architecture choices

- How do you decide between exposing something as an MCP tool or as an A2A agent? Has that choice ever gone wrong?
- When do you use `AgentTool`-style delegation (the orchestrator stays in charge) vs. handing the conversation off to a sub-agent?
- How many agents deep do your chains go in practice? Where does it stop being worth it?
- Is the extra latency from LLM-to-LLM calls acceptable for your users? How do you reduce it?

### 8. Ownership and organization

- Who gets paged when a multi-agent workflow fails at 2 a.m.: the orchestrator's team or the failing agent's team?
- Do agent teams offer SLAs or SLOs to other teams, like regular services do?
- How did you convince other teams to publish their agents over A2A?

## Open questions

-
