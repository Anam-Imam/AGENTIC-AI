# Company Decision & Support Policy

## Priority levels

- P1 Critical: service outage, major security incident, or issue affecting most users.
- P2 High: serious degradation affecting an important workflow, but the service remains partially usable.
- P3 Normal: standard operational issue with a workaround available.
- P4 Low: cosmetic issue, minor enhancement, or non-urgent request.

## Escalation policy

P1 incidents must be acknowledged immediately and escalated to the incident lead and engineering on-call team.

P2 incidents should be acknowledged within 30 minutes and escalated to the responsible service owner if the issue is not resolved promptly.

P3 and P4 requests can follow the normal support queue unless customer impact increases.

## Decision principles

When choosing between operational actions, prioritize:

1. User safety and data protection.
2. Reduction of customer impact.
3. Reversibility.
4. Evidence from monitoring, logs, and approved procedures.
5. Clear ownership and communication.

If evidence is incomplete, do not claim certainty. State what is known, unknown, and what evidence should be collected.

## Communication

For P1 and P2 incidents, the incident owner should provide concise status updates including current impact, known facts, action in progress, and the next expected update.

## Change management

Production changes should be reviewed before execution. High-risk changes should have a rollback plan and an identified owner.

Emergency changes may bypass normal review only when required to reduce immediate impact, but the change and rationale must be documented afterward.
