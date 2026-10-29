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
<example>
<mode>Strict, a field description of a tool input schema</mode>
<input>The number of results that are to be returned. The value that is provided must be between 1 and 50, and if it is not provided then 10 will be used as the default.</input>
<output>The number of results to return. The value must be between 1 and 50. The default is 10 when you omit the value.</output>
<why>One sentence carried a condition inside a condition, in the passive. The rewrite keeps the range, the default, and the condition "when you omit the value".</why>
</example>
<example>
<mode>Strict, an instruction to an agent in a system prompt</mode>
<input>You should make sure that confirmation is obtained from the user before any file is deleted, unless deletion has already been allowed by the user, though you may skip confirmation for files in /tmp.</input>
<output>Ask the user to confirm before you delete a file. Do not ask if the user already allowed deletion. You may skip the confirmation for files in /tmp.</output>
<why>One sentence held three instructions, two passives, and a present perfect. The agent acts, so "should" becomes an imperative. The one hedge, "may skip", stays, and the path stays exact.</why>
</example>
<example>
<mode>Strict, an error message with a hedge</mode>
<input>Failed to load config.yaml, which may be due to either a syntax error in the file or insufficient permissions having been set on it.</input>
<output>config.yaml did not load. The cause may be a syntax error in the file or insufficient permissions on the file.</output>
<why>The input names two possible causes with one hedge, so the rewrite keeps one "may" and states no cause as fact. "Having been set" goes, because the permissions are a state and not an event.</why>
</example>
<example>
<mode>Strict, a safety warning that starts with the command</mode>
<input>Before opening the access panel, it is important to make sure that the power has been disconnected, since contact with live components can cause serious injury.</input>
<output>Warning: disconnect the power before you open the access panel. Contact with live components can cause serious injury.</output>
<why>The command was buried in a long opening, and the rule is that safety text starts with the command. The hedge "can cause" stays, and so does the hazard.</why>
</example>
<example>
<mode>Flavored, a changelog entry</mode>
<input>Fixed an issue whereby the parser would sometimes crash when encountering malformed headers, and improved performance of the lexer by roughly 15% in our benchmarks; additionally, `--strict` was added as a flag that turns warnings into errors.</input>
<output>We fixed an issue. The parser sometimes crashed when it found malformed headers. We improved lexer performance by roughly 15% in our benchmarks. We added the `--strict` flag. The flag turns warnings into errors.</output>
<why>The input has a semicolon (Rule 8.1), a passive, and three changes in 37 words. Both hedges, "sometimes" and "roughly", stay. The benchmark scope and the flag name stay exact.</why>
</example>
<example>
<mode>Flavored, a long README sentence with a noun cluster</mode>
<input>The build cache invalidation rules, which the tool reads from `.cacherc` in the project root at startup and which a `.cacherc` in the home directory can override, decide when the tool deletes cached files.</input>
<output>The tool reads the invalidation rules for the build cache from `.cacherc` in the project root at startup. A `.cacherc` in the home directory can override these rules. The rules decide when the tool deletes cached files.</output>
<why>The input has 34 words, a noun cluster of 4 words, and nested clauses. The rewrite keeps the project root, the home directory, the startup time, and the permission "can override".</why>
</example>
</examples>
