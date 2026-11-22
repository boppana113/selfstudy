# Design Patterns

## When to use a pattern
Q: How many design patterns should a typical LLD interview answer use?
A: Zero to two. Reach for one only when the requirements call for it; three or more usually reads as over-engineering.
Why: Picture designing a library system. You add a Builder for Book, a Singleton for the catalog, and a Factory for members. Each one adds a class and some indirection, but none solves a problem the requirements raised. The interviewer sees ceremony, not design. Start with plain classes, then name a pattern when one falls out naturally.

Q: Which patterns come up most in LLD interviews?
A: Strategy most of all, then Observer and State machine. Factory and Decorator come up sometimes; Builder, Singleton, and Facade rarely matter.
Why: Strategy tests polymorphism and composition over inheritance, the core of what LLD rounds grade. Observer and State machine come from common prompts (notifications; vending machines, order workflows).

## Factory
Q: What does a Factory do, and when do you use one?
A: One method decides which concrete class to create from an input like a type string, and callers get back the interface. Use it when the concrete type varies and you don't want creation logic scattered across callers.
Why: A notification service supports email and SMS. Without a factory, five call sites each have `if channel == "email": EmailSender()`. Adding push means editing all five. With `SenderFactory.create(channel)`, adding push is one new class plus one line in the factory.
Flip: If there are only two types and one caller, a plain `if` is fine. Some interviewers see factories as Java-style ceremony.

Q: Is `NotificationFactory.create(type)` the GoF Factory Method pattern?
A: No, it's a simple factory: one static method with a conditional. GoF Factory Method has subclasses override a creation method, which is rare in interviews; "use a factory" means the simple version.

## Builder
Q: When is a Builder worth it?
A: When an object has many optional fields, so a constructor would take ten arguments with half of them null. Most interview entities have 2–4 required fields and don't need one.
Why: An HTTP client request has a URL, method, headers, a body, a timeout, retries, and auth. `Request(url, "GET", None, None, 30, None, token)` is unreadable. `Request.builder().url(u).timeout(30).auth(token).build()` names each field. A `ParkingSpot(id, size)` has no optional fields, so a builder only adds code.
Flip: In Python, keyword arguments or a dataclass with defaults do the same job, so Builder is rarely idiomatic there.

## Singleton
Q: The interviewer asks "should the ParkingLot be a Singleton?" What's the default answer?
A: Usually no. Create one instance and pass it through constructors; a Singleton hides the dependency and makes tests share global state.
Why: Tests for two parking lot scenarios both call `ParkingLot.get_instance()` and get the same object, so spots taken in test 1 are still taken in test 2. With constructor injection, each test builds its own lot. Say yes only if they explicitly want one shared instance across the whole system (config, logger).
Staff: In Python, a module-level object already acts as a singleton because modules load once.

## Decorator
Q: Messages can be logged, encrypted, or both, optionally per message. Subclasses or Decorator?
A: Decorator: wrap the base sender in `LoggingSender(EncryptingSender(base))`. Subclasses would need one class per combination, and the combinations multiply.
Why: With 3 optional behaviors (log, encrypt, compress), subclassing needs up to 7 combination classes like `LoggedEncryptedSender`. With decorators, it's 3 wrapper classes stacked as needed at runtime. Each wrapper implements the same interface and forwards to the one it wraps.
Flip: If the variation is fixed at design time and stable (a `Truck` is always a `Truck`), use a normal subclass. Note that wrapper order can matter (encrypt-then-log logs ciphertext).

## Facade
Q: What is a Facade, and do you need to name it in an interview?
A: A class that coordinates several components behind one simple interface, like a `Game` class over `Board`, `Player`, and rules. You build these anyway; naming it is optional.
Why: In tic-tac-toe, the caller calls `game.make_move(row, col)`. Behind it, `Game` places the mark on `Board`, checks for a win, and switches the current `Player`. The caller never touches Board directly. The name matters more when wrapping messy legacy code.

## Strategy
Q: Checkout has `if method == "card" ... elif method == "paypal" ...` in several places. How do you fix it?
A: Strategy: define a `PaymentMethod` interface with `pay(amount)`, one class per method, and have `Checkout` hold a reference and delegate to it. Adding a method means adding a class, not editing conditionals.
Why: Add Apple Pay with the if-chain: you edit `checkout`, `refund`, and `validate`, and miss one. With Strategy, you write `ApplePay(PaymentMethod)` with `pay` and `refund`, and `Checkout` never changes. That's open/closed in practice.

Q: Factory vs Strategy: what's the difference?
A: Factory decides which object to create. Strategy decides which behavior an existing object uses, swapped through composition. They often pair up: a factory builds the right strategy.
Why: A ride app prices trips by surge, flat, or subscription. `PricingFactory.create(user)` picks `SubscriptionPricing` once. The `Trip` object holds that strategy and calls `price.compute(distance)`; mid-trip, it could swap to `SurgePricing` without becoming a new Trip.

## Observer
Q: An order is placed, and inventory, email, and analytics all need to react. What pattern, and why?
A: Observer: the order service keeps a list of subscribers and calls `on_order_placed(order)` on each. It doesn't know what they do, so adding loyalty points is a new subscriber, not an edit to order code.
Why: Without Observer, `place_order` calls `inventory.reserve()`, `email.send()`, `analytics.track()` directly, and every new consumer edits it. With Observer, `place_order` saves the order and calls `notify()`; `LoyaltyService` attaches itself at startup.
Staff: In-process Observer is synchronous: a slow or throwing subscriber blocks or breaks the others. Across services, the same idea becomes a message queue or pub/sub topic.

## State machine
Q: A vending machine accepts coins, selection, and dispensing, and what's valid depends on its status. How do you design it?
A: State pattern: one class per state (`Idle`, `HasCoin`, `Dispensing`), each implementing every action. The machine delegates to its current state, and states set the next state. No switch on status in every method.
Why: A user presses "select" with no coin. `Idle.select()` says "insert coin first" and stays Idle. They insert a coin: `Idle.insert_coin()` moves the machine to `HasCoin`. Adding a `OutOfStock` state is one new class, not a new branch in four switch statements.
Staff: When a state machine is in the design, it's usually the centerpiece. Draw the state diagram (circles for states, arrows labeled with actions) before coding.

Q: What requirement cues point to a state machine?
A: The word "state" or "status" repeats, and which actions are valid depends on the current one: vending machines, document approval, order lifecycle, game turns.
