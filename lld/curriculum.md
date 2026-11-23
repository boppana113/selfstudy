# Low-Level Design Curriculum

Follows Hello Interview's LLD track: Delivery Framework → Core Concepts → Patterns → Problem Breakdowns.
Each topic lists the **testable points** that `/lld-pretest` and `/lld-drill` quiz on. Slugs for topics not yet pulled in are guesses; rename them to match the site when you get there.

Workflow per topic: `/lld-pretest <slug>` → read the Hello Interview page → `/lld-drill <slug>` → spaced reviews via `/lld-drill review`.

Interview format: an LLD round asks you to design the classes, interfaces, and key methods for a small system (parking lot, vending machine, elevator), usually with some code. You're graded on clean responsibilities and extensibility, not on scale.

---

## Phase 0: Delivery Framework

### `lld-delivery`: LLD Interview Delivery
- Order: clarify requirements → core entities/classes → relationships and interfaces → key methods / code → walk through a use case → extensions
- Scope down to 3–5 core use cases; state what you're leaving out
- Entities come from the nouns in the requirements, methods from the verbs
- Walk one concrete scenario through the design to prove it works
- Extensibility question at the end ("now add X"): a good design adds a class, not edits to five

---

## Phase 1: Core Concepts

### `design-principles`: Design Principles
- Apply them, don't recite them: interviewers grade the decisions, not the acronyms
- KISS: start with the simplest thing that works (a plain conditional before a Strategy); the most-violated principle in LLD rounds. Add complexity when simplicity breaks (a 500-line class, a new variant touching five places)
- DRY: one place for logic that is *conceptually* the same, not just textually similar; forced sharing creates coupling
- DRY vs KISS tradeoff: say it out loud ("keep it in `User` for now, extract a validator once it repeats 3–4 times"); naming the tension is the senior signal
- YAGNI: build only what the requirements ask; design with extension in mind but don't build ahead. "How would you extend this?" is where future features go
- Separation of concerns: display, input, and rules in separate classes so each change touches one class and each part is testable alone
- Law of Demeter: no `a.getB().getC().getD()` across different types; add a method on the near object instead. Fluent chains on the same object (builders) are fine
- SRP: one reason to change per class (content vs formatting vs storage)
- OCP: add a variant by adding a class behind an interface, not by editing an `if/elif` chain
- LSP: a subclass must work anywhere the parent does; a subclass throwing on an inherited method, or callers needing `isinstance` checks, means the hierarchy is wrong (move the capability into its own interface)
- ISP: small focused interfaces; empty or throwing method stubs are the smell
- DIP: business logic defines the interface it needs and implementations conform to it; the payoff is swapping implementations and testing with a mock. DIP is the principle, constructor injection is the technique
- SOLID is Java-era; outside Java/C# lean on composition and functions, and don't break KISS to satisfy SOLID

### `oop-concepts`: OOP Concepts
- Concepts show in the design, not in naming them: requirement cue → interface, private fields, no type checks
- Encapsulation: private state, changed only through methods that enforce invariants (no negative balance). Don't expose mutable internal collections; return a copy or read-only view. Default to a method over a public field
- Abstraction: callers depend on an interface (`PaymentMethod.process()`), not the concrete class. Reach for it where there's variation or messy logic. Right level: named after what the caller needs, not `doWork()`/`handleRequest()`, and not so specific it hides nothing
- Polymorphism: same call, each type handles itself; replaces `if type ==` and switches on enums, so a new type is a new class and the caller never changes. Tradeoff: many implementations make flow harder to trace and debug; be ready to defend explicit branches vs polymorphism
- Inheritance: shares implementation but couples tightly (fragile base class). Fits only stable, shared implementation where subclasses don't break the parent's contract (account types sharing balance logic)
- The classic mistake: inheritance to model behavior variation (`ElectricCar` overriding `start_engine`; where does hybrid go?). Fix: pull the varying behavior into an interface and compose it (a `Drivetrain` passed into `Car`)
- Default to interfaces + composition; most LLD interviews need no inheritance at all

### `design-patterns`: Design Patterns
- Use a pattern only when the problem calls for it; three or more patterns in one design usually means over-engineering
- Most-asked: Strategy (#1), Observer, State machine; then Factory, Decorator; Builder, Singleton, Facade rarely matter
- Creational: Factory (one place picks the concrete class; "simple factory", not GoF Factory Method), Builder (many optional fields), Singleton (usually avoid; pass shared objects in instead)
- Structural: Decorator (stack optional behaviors at runtime without a subclass per combination), Facade (an orchestrator class that hides a subsystem; you build it anyway)
- Behavioral: Strategy (swap an algorithm through composition, kills `if type ==` chains), Observer (subject notifies subscribers; no knowledge of what they do), State machine (each state is a class; transitions owned by states)
- Contrasts: Factory picks *which object to create* vs Strategy picks *which behavior an existing object uses*; Decorator (runtime, combinable) vs subclass (fixed at design time)
- Spotting cues in requirements: "different types/methods" → Strategy or Factory; "notify", "multiple components react" → Observer; "state" repeated, valid actions depend on status → State machine; "optional, combinable features" → Decorator
- Drawing a state diagram (states + labeled transitions) is the best way to present a state machine
- Regional difference: US interviews grade design quality and rarely ask for pattern names; some regions (e.g. India) ask about patterns directly

### `concurrency-lld`: Concurrency in LLD
- Shared mutable state, race conditions, locks vs atomic operations
- Where locks go in a design (e.g. reserving a parking spot, booking a seat)
- Thread-safe collections, producer/consumer queues

---

## Phase 2: Problem Breakdowns (use `/lld-drill` in scenario mode, or mock-style)

Common problems: `parking-lot`, `tic-tac-toe`, `vending-machine`, `elevator`, `library-management`, `rate-limiter-lld`, `lru-cache`, `chess`, `splitwise`, `movie-booking`.
