# Object-Oriented Design, from Scratch to Specialist

This series teaches object-oriented design (OOD) the way you'd actually use it: in a 45-minute interview, and in production code. It starts with what an object even is and ends with designing systems like ATMs, elevators and ticketing platforms, with real concurrency problems, extensibility follow-ups and the trade-offs a senior engineer would talk about.

Every post is standalone and written for beginners, but none of them stop at the basics. Each case study comes with:

- **A runnable Python solution** (standard library only, Python 3.13): the design I'd recommend, with its reasoning.
- **Alternative designs, side by side.** For every major decision (if/else vs Strategy, enum vs State pattern, global lock vs seat holds…) you get code for each option, a comparison table and a recommendation.
- **Real-world context.** How parking garages, Ticketmaster, Otis elevators, Amazon lockers, ATM networks and restaurant POS systems actually solve the same problem.
- **Tests** you can run, and **"Test yourself" questions** at the end of each post.

## Learning path

The series goes from concepts, to patterns, to interview skills, to practice. Each post assumes only what the earlier ones taught, so reading in order works even if you've never written a class. The case studies get harder roughly in order and refer back to the foundations.

### Part 1: Foundations

| # | Post | What you'll learn |
|---|---|---|
| 1 | [OOP Fundamentals](01-foundations/01-oop-fundamentals.md) | From your first class to the four pillars, class relationships, SOLID and Python's object model |
| 2 | [Design Patterns for OOD](01-foundations/02-design-patterns.md) | Strategy, State, Observer, Factory, Command and more: what each one is built from, and when *not* to use it |
| 3 | [What Is an OOD Interview?](01-foundations/03-what-is-an-ood-interview.md) | Turning that knowledge into a live performance: what interviewers score and how it differs from coding and system-design rounds |
| 4 | [The OOD Interview Framework](01-foundations/04-the-ood-interview-framework.md) | The repeatable process every case study follows: requirements → objects → class diagram → code → extensions |

> **Already comfortable with OOP and patterns?** Start at post 3, and use posts 1–2 as a reference.

### Part 2: Case studies

| # | Case study | Core design challenges | Patterns in the recommended design |
|---|---|---|---|
| 1 | [Parking Lot](02-case-studies/01-parking-lot/README.md) | Spot allocation, fee calculation, vehicle–spot compatibility | Strategy, Decorator, Facade |
| 2 | [Movie Ticket Booking](02-case-studies/02-movie-ticket-booking/README.md) | Preventing double booking, seat holds, pricing | Strategy, per-screening locks + seat holds |
| 3 | [Unix File Search](02-case-studies/03-unix-file-search/README.md) | Composable filters, tree traversal, lazy results | Composite, Specification, Iterator |
| 4 | [Vending Machine](02-case-studies/04-vending-machine/README.md) | Machine states, making change, inventory | State, Strategy |
| 5 | [Elevator System](02-case-studies/05-elevator-system/README.md) | Scheduling, multi-car dispatch, simulation | Strategy, Observer, transition table |
| 6 | [Grocery Store](02-case-studies/06-grocery-store/README.md) | Promotion engine, money handling, receipts | Specification, Strategy |
| 7 | [Tic Tac Toe](02-case-studies/07-tic-tac-toe/README.md) | Win detection, AI players, separating logic from I/O | Strategy, Adapter |
| 8 | [Blackjack](02-case-studies/08-blackjack/README.md) | Hand values with aces, dealer vs player, round flow | Strategy, transition table |
| 9 | [Shipping Locker](02-case-studies/09-shipping-locker/README.md) | Compartment assignment, access codes, expiry | Strategy, Observer, Factory |
| 10 | [ATM](02-case-studies/10-atm/README.md) | Session states, cash dispensing, debit/dispense consistency | State, Command |
| 11 | [Restaurant Management](02-case-studies/11-restaurant-management/README.md) | Reservations, kitchen orders, bill splitting | Observer, Strategy |

## Running the code

Everything uses only the Python standard library, so there's nothing to install.

```bash
cd object-oriented-design/02-case-studies/01-parking-lot
python3 parking_lot.py                 # run the demo
python3 alternatives.py                # run the competing designs
python3 -m unittest -v                 # run the tests
```

To run every test in the series from the repository root:

```bash
for d in object-oriented-design/01-foundations/code object-oriented-design/02-case-studies/*/; do python3 -m unittest discover -s "$d"; done
```

## Sources

These posts are my own write-ups, built on the topic list of ByteByteGo's *Object-Oriented Design Interview* course, the "Gang of Four" *Design Patterns* book, and public material on how the real systems work. All explanations and code are original.
