# Spec: appointment booking

Patients pick a slot, confirm, and get a reminder. Staff see the day's calendar.

## Constraints

- The system must never double-book a practitioner.
- The system must never email a patient without recorded consent.
- Slots are 15 minutes and align to the clinic's opening hours.

## Acceptance criteria

- AC-1 Booking a taken slot returns a conflict and leaves the calendar unchanged.
- AC-2 Cancelling frees the slot within one second.
- AC-3 A reminder goes out 24 hours before the slot, once.
