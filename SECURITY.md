# Security policy

Report vulnerabilities through GitHub private vulnerability reporting. Include
the affected commit, the obligation, the expected verdict, the observed verdict,
and the counterexample if one was produced.

This tool performs exhaustive analysis over small, finite models entirely
in-process. It opens no network connections, spawns no subprocesses, and reads
no untrusted input while verifying. A `verified` result is a proof *for the
committed model*, not for any real system: the value of the tool is only as good
as the fidelity of the model to the design it abstracts.

The models are intentionally small so the state space can be explored in full.
Three obligations model deliberately broken designs and must be refuted; a
`verified` result on one of those would itself be a bug in the checker and should
be reported.

Do not treat these models as specifications of production systems. They
illustrate a method — proving safety properties and producing counterexamples —
over synthetic security designs.
