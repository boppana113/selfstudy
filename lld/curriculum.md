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

### `oop-concepts`: OOP Concepts
- Encapsulation: state is private, changed only through methods that keep it valid
- Abstraction: callers depend on an interface, not the concrete class
- Inheritance vs composition: "is-a" vs "has-a"; prefer composition, inheritance for stable type hierarchies only
- Polymorphism: one call, behavior picked by the object's type; replaces type-switch conditionals
- Interfaces / abstract classes and when each fits

### `design-principles`: Design Principles
- SOLID, especially single responsibility and open/closed (add behavior by adding a class)
- Dependency inversion: depend on abstractions, inject collaborators through the constructor
- DRY, KISS, YAGNI: and how YAGNI argues against speculative patterns
- Low coupling, high cohesion; law of Demeter

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
