# More Examples

<examples>
<example>
<mode>Strict, a tool description</mode>
<input>This tool will attempt to synchronize state across the various backends that have been configured, and if a conflict is detected it may resolve it automatically depending on the strategy that has been set, or otherwise it will surface the conflict for manual review.</input>
<output>The tool tries to synchronize state across the configured backends. If it finds a conflict, it may resolve the conflict automatically, depending on the configured strategy. If the tool does not resolve the conflict, it reports the conflict for manual review.</output>
<why>Two actions and two compound tenses in 44 words. "Will attempt to" becomes "tries to", and "may resolve" stays, so the rewrite promises only an attempt. The last sentence branches on whether the tool resolved the conflict, because "or otherwise" also covers a permitted resolution that did not occur.</why>
</example>
<example>
<mode>Flavored, a README paragraph</mode>
<input>Our caching layer is designed to slot seamlessly into your existing stack with minimal friction and no vendor lock-in; it leverages semantic similarity to dramatically reduce the cache misses that traditionally plague LLM workloads.</input>
<output>We designed our caching layer to fit into your current stack without vendor lock-in. It uses semantic similarity to reduce cache misses, a long-standing problem for LLM workloads.</output>
<why>The semicolon, the claims with no measurement ("seamlessly", "minimal friction", "dramatically"), and the soft verbs ("slot into", "leverages") go. "Designed to" stays, because the source states a goal, and a goal is weaker than a result.</why>
</example>
</examples>
