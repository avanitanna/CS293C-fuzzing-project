# CS293C-fuzzing-project


Project: Mutant Guided Fuzzing
By: Avani Tanna, Animesh Dangwal

Coverage-based approaches are used as a way to guide fuzzers to generate inputs to explore paths [1,2]. Coverage is also a popular metric used to measure the effectiveness of fuzzers[1,2]. However, it is widely agreed that coverage is not enough in guiding a fuzzer due to coverage saturation [3] and it is also not enough for evaluating fuzzers [4]. Recent research [3,4,5] introduces new metrics that might be more realistic than coverage to evaluate a fuzzer. We investigate mutant analysis. Typically in mutant analysis, we measure the effectiveness of a fuzzer through the number of mutants killed. With our project, we aim to use mutant analysis not just for comparing fuzzers, but as a guide to generate better inputs which can potentially kill more mutants.

Problem Statement:
We develop and design a mutant guided fuzzing technique, analogous to coverage guided fuzzing techniques. For our project we focus on grammar-based fuzzing techniques. Similar to how grammar-based fuzzers typically use coverage to guide their input generation, we take inputs that were known to kill mutants and feed them back to the fuzzer. In support of the idea that ‘interesting’ inputs (known mutant killers) can be used and mutated (via probabilistic grammar) to further generate more interesting inputs to kill mutants.

Tentative Workflow:
We initially explore mutant generation (using techniques from the fuzzing book) for python’s json parser, html parser (https://github.com/html5lib/html5lib-python), and css parser (https://tinycss.readthedocs.io/en/latest/). We also compare the grammar-based fuzzer variations for the same parsers. Based on the deaths, we only keep inputs that killed mutants and discard the rest. These inputs are then changed based on the fuzzing technique, i.e. for grammar-based fuzzing, we generate probabilistic weight vectors that are re-calculated based on an empirical probability distribution to then further generate the input population.

The following are popular mutations[6][7] used in mutant analysis:
Dropping statements
Replace a statement with a pass, return, break, continue or delete entirely 
Changing branches
Negate the branch condition
Replace the >= with just > or just ==
Replace <= with just < or just ==
Delete the else branches
Changing operators
Changing arithmetic operators
Removing brackets
Replace constants
Change globals to locals, vice versa
Increment/decrement constant values
Left/right shift constant values

Change/break out of loops
Change loop conditions (similar to branch mutations)
Break out of loop after random n iterations.
Data structure changes
Convert list to dict, vice versa
Reverse a list
Delete elements from a list, dict 
Due to our experiments focusing on parsers specifically, we pick dropping statements, data structure changes, branch changes, constant changes, loop changes as our mutations.

Experiments:
We aim to compare our mutant guided fuzzing technique with the fuzzingbook-provided probabilistic grammar technique based on “quality” of inputs generated. We define quality here as a combination of coverage and mutant score. We focus on inputs that cover the same parts of code (have the same coverage score) and compare them with the number of mutants killed. This acts as a way to show the quality of inputs with respect to how many mutants it could kill while having the same amount of coverage. 

We also focus on measuring how many more mutants are killed by fuzzers (say using a score). These are mutants who survive fuzzing even after maximum possible coverage is reached. The number of mutants killed would show whether or not mutant guided fuzzing works better after coverage saturation, i.e. after maximum (possible) coverage is reached and guidance based on coverage becomes useless. This measure would act as a baseline to prove our hypothesis that inputs that have killed mutants before can be modified to kill more mutants. 

Expected Results:
We hope to show that mutant-based coverage can help kill mutants, and also generate higher quality inputs even after coverage saturation. Thus, by extension of the assumptions of the coupling effect and the competent programmer, show that mutant guided fuzzing is a more realistic approach for guiding a fuzzer than coverage guided fuzzing. 

References:
1. https://dl.acm.org/doi/10.1145/3238147.3238176 
2. https://www.fuzzingbook.org/ 
3. https://www.mdpi.com/2079-9292/10/16/1921 
4. https://ieeexplore.ieee.org/document/9282794 
5. https://arxiv.org/pdf/2201.11303.pdf
6.https://www.researchgate.net/publication/2590658_Design_Of_Mutant_Operators_For_The_C_Programming_Language
7. https://dl.acm.org/doi/pdf/10.1145/2635868.2635929 
 
