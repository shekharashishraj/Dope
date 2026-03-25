#!/usr/bin/env python3
"""
Build SET_D_perturbation.json from SET_D.tex and SET_D_answer_key.tex.
Generates 3 perturbations per question (one per wrong option) following
the grouped MCQ prompt strategy: replacement stem makes that option correct.
"""
import json
import os

# Base path for file_paths in output
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Questions extracted from SET_D.tex; gold answers from SET_D_answer_key.tex
# Format: (latex_stem_text, stem_text_plain, options_dict, gold_answer)
QUESTIONS_DATA = [
    (
        "Which set is this?",
        "Which set is this?",
        {"A": "A", "B": "B", "C": "C", "D": "D"},
        "D",
    ),
    (
        "Suppose two standard non-zero TF-IDF vectors have cosine similarity $-0.2$. What does this imply?",
        "Suppose two standard non-zero TF-IDF vectors have cosine similarity -0.2. What does this imply?",
        {
            "A": "The documents are strongly unrelated in topic",
            "B": "They have negatively correlated term weights",
            "C": "The similarity computation was implemented incorrectly",
            "D": "The documents share no terms",
        },
        "C",
    ),
    (
        "Why do deeper networks require careful initialization?",
        "Why do deeper networks require careful initialization?",
        {
            "A": "To control gradient scale across layers",
            "B": "To decrease the vocabulary size of inputs",
            "C": "To simplify the objective function",
            "D": "To remove recurrence from the model",
        },
        "A",
    ),
    (
        "Stacking multiple linear layers without activations results in:",
        "Stacking multiple linear layers without activations results in:",
        {
            "A": "Implicit regularization of weights",
            "B": "Exponentially more expressive representations",
            "C": "Increased ability to model hierarchical structure",
            "D": "A model equivalent to a single linear transformation",
        },
        "D",
    ),
    (
        "Why do vanilla RNNs struggle with long-range dependencies?",
        "Why do vanilla RNNs struggle with long-range dependencies?",
        {
            "A": "The hidden state has fixed dimensionality",
            "B": "They reuse identical parameters at every time step",
            "C": "Gradients decay or explode during backpropagation",
            "D": "They produce outputs only at the final step",
        },
        "C",
    ),
    (
        "Why does the Markov assumption reduce sparsity in N-gram models?",
        "Why does the Markov assumption reduce sparsity in N-gram models?",
        {
            "A": "It removes independence assumptions",
            "B": "It restricts conditioning context",
            "C": "It increases vocabulary size",
            "D": "It enforces smoothing",
        },
        "B",
    ),
    (
        "A two-layer neural network with step activations can represent the XOR function. However, when trained with gradient descent, it fails to learn XOR. What best explains this discrepancy?",
        "A two-layer neural network with step activations can represent the XOR function. However, when trained with gradient descent, it fails to learn XOR. What best explains this discrepancy?",
        {
            "A": "Step activations are insufficient to represent nonlinear decision boundaries",
            "B": "The loss function is not convex for XOR",
            "C": "The network requires more hidden units to separate XOR",
            "D": "The activation provides no useful local gradient signal for weight updates",
        },
        "D",
    ),
    (
        "A neural language model is trained on the phrases ``small red car'' and ``large blue truck.'' During testing, it assigns meaningful probability mass to ``small blue car,'' which never appeared in training. What most directly enables this generalization?",
        "A neural language model is trained on the phrases \"small red car\" and \"large blue truck.\" During testing, it assigns meaningful probability mass to \"small blue car,\" which never appeared in training. What most directly enables this generalization?",
        {
            "A": "The model stores all observed word pairs explicitly",
            "B": "Embeddings capture semantics that combine compositionally",
            "C": "The softmax layer guarantees coverage of unseen sequences",
            "D": "Training implicitly includes all possible word permutations",
        },
        "B",
    ),
    (
        "A TF-IDF retrieval system often misses semantically equivalent documents with synonyms. The primary limitation is:",
        "A TF-IDF retrieval system often misses semantically equivalent documents with synonyms. The primary limitation is:",
        {
            "A": "Bag-of-Words representation assumes term independence",
            "B": "IDF overweights rare tokens",
            "C": "Document length normalization distorts similarity",
            "D": "Cosine similarity ignores magnitude differences",
        },
        "A",
    ),
    (
        "Increasing model size worsens test performance while improving training accuracy. This suggests:",
        "Increasing model size worsens test performance while improving training accuracy. This suggests:",
        {
            "A": "Optimization failure",
            "B": "Underfitting",
            "C": "Overfitting",
            "D": "Over-regularization",
        },
        "C",
    ),
    (
        "When computing the loss at time $t$ in an RNN, what differs from a feed-forward network?",
        "When computing the loss at time t in an RNN, what differs from a feed-forward network?",
        {
            "A": "The RNN uses different weights at each step",
            "B": "The RNN ignores its previous hidden state",
            "C": "The RNN does not produce outputs at intermediate steps",
            "D": "The loss depends on the hidden state from time $t-1$ and the same weight matrices are reused across all time steps",
        },
        "D",
    ),
    (
        "L2 regularization improves generalization primarily by:",
        "L2 regularization improves generalization primarily by:",
        {
            "A": "Forcing sparse parameter updates",
            "B": "Encouraging smaller weight magnitudes",
            "C": "Reducing the number of layers in the network",
            "D": "Eliminating bias terms",
        },
        "B",
    ),
    (
        "A sigmoid neuron slows learning when its activation saturates because:",
        "A sigmoid neuron slows learning when its activation saturates because:",
        {
            "A": "Bias parameters stop updating",
            "B": "Gradients become very small in extreme regions",
            "C": "Weight magnitudes increase uncontrollably",
            "D": "Its output becomes approximately linear",
        },
        "B",
    ),
    (
        "RNN models share parameters across time steps. Compared to a model with independent parameters at each step, weight reuse primarily:",
        "RNN models share parameters across time steps. Compared to a model with independent parameters at each step, weight reuse primarily:",
        {
            "A": "Allows parallel computation across sequence positions",
            "B": "Eliminates vanishing gradients through parameter averaging",
            "C": "Increases model capacity by expanding representational depth",
            "D": "Reduces parameters and shares the same transformation",
        },
        "D",
    ),
    (
        "In RNN language modeling, the typical training loss is:",
        "In RNN language modeling, the typical training loss is:",
        {
            "A": "Cross-entropy over the vocabulary",
            "B": "Smooth L1 over embeddings",
            "C": "Hinge loss over tags",
            "D": "Binary cross-entropy per position",
        },
        "A",
    ),
    (
        "Suppose a document is tokenized at the sentence level (each entire sentence is one token). What impact does this have on vocabulary size and sequence length?",
        "Suppose a document is tokenized at the sentence level (each entire sentence is one token). What impact does this have on vocabulary size and sequence length?",
        {
            "A": "Both vocabulary size and sequence length decrease",
            "B": "Vocabulary size increases dramatically, and sequence length becomes very short",
            "C": "Both vocabulary size and sequence length increase",
            "D": "Vocabulary size decreases dramatically, and sequence length becomes extremely long",
        },
        "B",
    ),
    (
        "Why must an RNN be unrolled across time during training?",
        "Why must an RNN be unrolled across time during training?",
        {
            "A": "To allocate separate parameters for each time step",
            "B": "To represent recurrence as a time-indexed differentiable graph",
            "C": "To remove weight sharing across sequence positions",
            "D": "To increase hidden state dimensional capacity",
        },
        "B",
    ),
    (
        "LSTMs mitigate basic RNN issues mainly by:",
        "LSTMs mitigate basic RNN issues mainly by:",
        {
            "A": "Freezing the recurrent matrix $U$",
            "B": "Introducing gated operations",
            "C": "Using convolution instead of recurrence",
            "D": "Removing nonlinearity between layers",
        },
        "B",
    ),
    (
        "Which NLP architecture would be suitable for identifying the NER type for ``Ben'' in ``Ben \\& Jerry's ice cream is good''?",
        "Which NLP architecture would be suitable for identifying the NER type for \"Ben\" in \"Ben & Jerry's ice cream is good\"?",
        {
            "A": "BiLSTM",
            "B": "Word2Vec + Decoder RNN",
            "C": "Bag-of-Words + Naive Bayes",
            "D": "Hidden Markov Models",
        },
        "A",
    ),
    (
        "A 3-layer neural network with ReLU activations outputs only zeros for all inputs after initialization. What is the most likely cause?",
        "A 3-layer neural network with ReLU activations outputs only zeros for all inputs after initialization. What is the most likely cause?",
        {
            "A": "Cross-entropy loss misconfigured",
            "B": "The final layer is using Softmax without temperature scaling",
            "C": "Learning rate too high",
            "D": "All pre-activation values are negative in the first layer",
        },
        "D",
    ),
    (
        "A 3-layer neural network with ReLU activations outputs a fixed, non-zero output for all inputs. What is the most likely cause?",
        "A 3-layer neural network with ReLU activations outputs a fixed, non-zero output for all inputs. What is the most likely cause?",
        {
            "A": "Dropout disabled",
            "B": "The input data has not been normalized",
            "C": "All weights are initialized to zero while biases are non-zero",
            "D": "Learning rate too high",
        },
        "C",
    ),
    (
        "Compared to full-batch gradient descent, SGD introduces:",
        "Compared to full-batch gradient descent, SGD introduces:",
        {
            "A": "Biased gradient estimates but lower variance",
            "B": "Deterministic updates with faster convergence",
            "C": "Unbiased gradient estimates with higher variance",
            "D": "Smaller parameter magnitudes",
        },
        "C",
    ),
    (
        "Why does BPE reduce out-of-vocabulary issues?",
        "Why does BPE reduce out-of-vocabulary issues?",
        {
            "A": "It removes infrequent words from the vocabulary",
            "B": "It increases vocabulary size",
            "C": "It decomposes rare words into subword units",
            "D": "It converts tokens into fixed-length character blocks",
        },
        "C",
    ),
    (
        "A sequence model trained with teacher forcing performs well during training but poorly during inference. The most likely explanation is:",
        "A sequence model trained with teacher forcing performs well during training but poorly during inference. The most likely explanation is:",
        {
            "A": "Cross-entropy loss over-penalizes rare tokens during decoding",
            "B": "The model experiences exposure bias due to distribution mismatch",
            "C": "The hidden state dimensionality is insufficient for long sequences",
            "D": "The optimizer fails to converge to a global minimum",
        },
        "B",
    ),
    (
        "In standard LSTMs, which component carries long-term summary information?",
        "In standard LSTMs, which component carries long-term summary information?",
        {
            "A": "Input embeddings",
            "B": "Output logits",
            "C": "Cell state $c$",
            "D": "Hidden state $h$",
        },
        "C",
    ),
    (
        "Two non-zero TF--IDF document vectors have cosine similarity $0$. What does this imply?",
        "Two non-zero TF-IDF document vectors have cosine similarity 0. What does this imply?",
        {
            "A": "Their Euclidean distance must be maximal",
            "B": "The documents have different lengths",
            "C": "The documents are unrelated in meaning",
            "D": "The documents share no common terms",
        },
        "D",
    ),
    (
        "A tokenizer converts a sentence into a sequence like: \\([12408, 6391, 4014, 316, 1001]\\). What best explains why tokens are converted into this form?",
        "A tokenizer converts a sentence into a sequence like [12408, 6391, 4014, 316, 1001]. What best explains why tokens are converted into this form?",
        {
            "A": "To enable the model to process text as numerical input based on a fixed vocabulary mapping",
            "B": "To ensure every word has a single unchanging meaning",
            "C": "To compress the sentence into a shorter representation",
            "D": "To remove grammatical ambiguity before training",
        },
        "A",
    ),
    (
        "What is the probability of the sequence $H \\rightarrow C \\rightarrow H$? Given:\n"
        "\\[\n"
        "P(H \\rightarrow H) = 0.7,\\quad\n"
        "P(H \\rightarrow C) = 0.3,\\quad\n"
        "P(C \\rightarrow H) = 0.4,\\quad\n"
        "P(C \\rightarrow C) = 0.6,\n"
        "\\]\n"
        "with initial probabilities \\(P(H) = 0.5, P(C) = 0.5\\).",
        "What is the probability of the sequence H -> C -> H? (Given transition and initial probabilities.)",
        {
            "A": "$0.12$",
            "B": "$0.06$",
            "C": "$0.21$",
            "D": "$0.042$",
        },
        "B",
    ),
    (
        "A language model achieves lower perplexity than another model but performs worse on question answering. The most principled explanation is:",
        "A language model achieves lower perplexity than another model but performs worse on question answering. The most principled explanation is:",
        {
            "A": "Lower perplexity always indicates overfitting to training data",
            "B": "Perplexity ignores normalization across token positions",
            "C": "Question answering requires larger vocabularies than modeling",
            "D": "Perplexity reflects intrinsic likelihood rather than task utility",
        },
        "D",
    ),
    (
        "During training, a neural network's loss decreases for a few iterations, then begins oscillating widely without converging. Which explanation is most consistent with this behavior?",
        "During training, a neural network's loss decreases for a few iterations, then begins oscillating widely without converging. Which explanation is most consistent with this behavior?",
        {
            "A": "The batch size is too small, increasing gradient variability",
            "B": "The batch size is too large, reducing gradient noise",
            "C": "The learning rate is too small to escape local minima",
            "D": "The learning rate is too large for the local loss curvature",
        },
        "D",
    ),
    (
        "Consider a 4-word sequence $W = (w_1, w_2, w_3, w_4)$ with probabilities\n"
        "\\[\n"
        "P(w_1) = 0.5,\\quad\n"
        "P(w_2 \\mid w_1) = 0.4,\\quad\n"
        "P(w_3 \\mid w_1, w_2) = 0.2,\\quad\n"
        "P(w_4 \\mid w_1, w_2, w_3) = 0.1.\n"
        "\\]\n"
        "What is the perplexity of the sequence?",
        "Consider a 4-word sequence with given conditional probabilities. What is the perplexity of the sequence?",
        {
            "A": "$4.215$",
            "B": "$2.154$",
            "C": "$5.000$",
            "D": "$3.976$",
        },
        "D",
    ),
    (
        "A system has two states, $A$ and $B$, with the following transition probabilities:\n"
        "\\begin{itemize}\n"
        "    \\item If in $A$: stays in $A$ with probability $0.6$ (and goes to $B$ with probability $0.4$)\n"
        "    \\item If in $B$: stays in $B$ with probability $0.4$ (and goes to $A$ with probability $0.6$)\n"
        "\\end{itemize}\n"
        "Suppose the system starts in state $B$. As the number of transitions approaches infinity, what is the most accurate statement?",
        "A system has two states A and B with given transition probabilities; it starts in B. As transitions approach infinity, what is the most accurate statement?",
        {
            "A": "The state probabilities converge to a fixed stationary distribution",
            "B": "The state probabilities continue fluctuating without convergence",
            "C": "The limiting distribution depends on the initial state",
            "D": "The chain eventually remains permanently in one state",
        },
        "A",
    ),
    (
        "In the Word2Vec skip-gram model with negative sampling, which of the following best describes the optimization objective for a target word $w$ and a context word $c$?",
        "In the Word2Vec skip-gram model with negative sampling, which best describes the optimization objective for a target word w and context word c?",
        {
            "A": "Minimize the squared Euclidean distance between embeddings of all words in the same document",
            "B": "Maximize $\\log \\sigma(v_c^\\top v_w) + \\sum_{i=1}^{k} \\log \\sigma(-v_{n_i}^\\top v_w)$",
            "C": "Maximize cosine similarity between all word pairs within a fixed window",
            "D": "Maximize $\\log P(c \\mid w)$ using a full softmax over the vocabulary",
        },
        "B",
    ),
    (
        "What fundamentally distinguishes ELMo embeddings from Word2Vec?",
        "What fundamentally distinguishes ELMo embeddings from Word2Vec?",
        {
            "A": "It represents words using character-level frequency features",
            "B": "It learns embeddings solely from global co-occurrence statistics",
            "C": "It produces context-dependent representations of words",
            "D": "It assigns a single fixed vector to each word type",
        },
        "C",
    ),
]

# For each question, (target_wrong_answer -> (replacement_substring, reasoning))
# Strategy: replacement stem asks/states something that makes that option the only correct one.
PERTURBATIONS = {
    1: {
        "A": ("Which option is the first letter of the alphabet?", "The stem asks which option is the first letter; only A is, so A becomes correct."),
        "B": ("Which option is the second letter of the alphabet?", "The stem asks which option is the second letter; only B is, so B becomes correct."),
        "C": ("Which option is the third letter of the alphabet?", "The stem asks which option is the third letter; only C is, so C becomes correct."),
    },
    2: {
        "A": ("Which statement describes documents that are strongly unrelated in topic?", "Option A states the documents are strongly unrelated in topic; the new stem asks for this, making A correct."),
        "B": ("Which statement describes negatively correlated term weights between two TF-IDF vectors?", "Option B states they have negatively correlated term weights; the new stem asks for this, making B correct."),
        "D": ("Which option indicates that the two documents share no terms?", "Option D states the documents share no terms; the new stem asks for this, making D correct."),
    },
    3: {
        "B": ("Which goal is to decrease the vocabulary size of inputs?", "Option B describes decreasing vocabulary size; the new stem asks for this, making B correct."),
        "C": ("Which option describes simplifying the objective function?", "Option C states simplifying the objective; the new stem asks for this, making C correct."),
        "D": ("Which option is about removing recurrence from the model?", "Option D states removing recurrence; the new stem asks for this, making D correct."),
    },
    4: {
        "A": ("Which outcome corresponds to implicit regularization of weights?", "Option A describes implicit regularization; the new stem asks for this, making A correct."),
        "B": ("Which outcome describes exponentially more expressive representations?", "Option B describes exponentially more expressive representations; the new stem asks for this, making B correct."),
        "C": ("Which outcome claims increased ability to model hierarchical structure?", "Option C describes modeling hierarchical structure; the new stem asks for this, making C correct."),
    },
    5: {
        "A": ("Which explanation focuses on the hidden state having fixed dimensionality?", "Option A states the hidden state has fixed dimensionality; the new stem asks for this, making A correct."),
        "B": ("Which option emphasizes reusing identical parameters at every time step?", "Option B states they reuse identical parameters at every step; the new stem asks for this, making B correct."),
        "D": ("Which option claims that outputs are produced only at the final step?", "Option D states they produce outputs only at the final step; the new stem asks for this, making D correct."),
    },
    6: {
        "A": ("Which effect is described as removing independence assumptions?", "Option A states it removes independence assumptions; the new stem asks for this, making A correct."),
        "C": ("Which option claims that the Markov assumption increases vocabulary size?", "Option C states it increases vocabulary size; the new stem asks for this, making C correct."),
        "D": ("Which option states that the Markov assumption enforces smoothing?", "Option D states it enforces smoothing; the new stem asks for this, making D correct."),
    },
    7: {
        "A": ("Which explanation claims that step activations are insufficient for nonlinear decision boundaries?", "Option A states step activations are insufficient for nonlinear boundaries; the new stem asks for this, making A correct."),
        "B": ("Which option attributes the failure to the loss function not being convex for XOR?", "Option B states the loss is not convex for XOR; the new stem asks for this, making B correct."),
        "C": ("Which explanation claims that more hidden units are required to separate XOR?", "Option C states more hidden units are required; the new stem asks for this, making C correct."),
    },
    8: {
        "A": ("Which option says the model stores all observed word pairs explicitly?", "Option A states the model stores all observed word pairs; the new stem asks for this, making A correct."),
        "C": ("Which answer credits the softmax layer with guaranteeing coverage of unseen sequences?", "Option C states the softmax guarantees coverage of unseen sequences; the new stem asks for this, making C correct."),
        "D": ("Which explanation claims that training implicitly includes all possible word permutations?", "Option D states training implicitly includes all permutations; the new stem asks for this, making D correct."),
    },
    9: {
        "B": ("Which explanation blames IDF for overweighting rare tokens?", "Option B states IDF overweights rare tokens; the new stem asks for this, making B correct."),
        "C": ("Which answer states that document length normalization distorts similarity?", "Option C states document length normalization distorts similarity; the new stem asks for this, making C correct."),
        "D": ("Which option claims that cosine similarity ignores magnitude differences?", "Option D states cosine similarity ignores magnitude; the new stem asks for this, making D correct."),
    },
    10: {
        "A": ("Which diagnosis points to optimization failure?", "Option A states optimization failure; the new stem asks for this, making A correct."),
        "B": ("Which option identifies the situation as underfitting?", "Option B states underfitting; the new stem asks for this, making B correct."),
        "D": ("Which explanation attributes the behavior to over-regularization?", "Option D states over-regularization; the new stem asks for this, making D correct."),
    },
    11: {
        "A": ("Which option claims that the RNN uses different weights at each step?", "Option A states the RNN uses different weights at each step; the new stem asks for this, making A correct."),
        "B": ("Which explanation says the RNN ignores its previous hidden state when computing the loss?", "Option B states the RNN ignores its previous hidden state; the new stem asks for this, making B correct."),
        "C": ("Which answer claims that the RNN does not produce outputs at intermediate steps?", "Option C states no outputs at intermediate steps; the new stem asks for this, making C correct."),
    },
    12: {
        "A": ("Which option states that L2 forces sparse parameter updates?", "Option A states L2 forces sparse updates; the new stem asks for this, making A correct."),
        "C": ("Which effect is described as reducing the number of layers in the network?", "Option C states reducing the number of layers; the new stem asks for this, making C correct."),
        "D": ("Which explanation says L2 eliminates bias terms?", "Option D states L2 eliminates bias terms; the new stem asks for this, making D correct."),
    },
    13: {
        "A": ("Which explanation claims that bias parameters stop updating in this regime?", "Option A states bias parameters stop updating; the new stem asks for this, making A correct."),
        "C": ("Which option blames uncontrolled increases in weight magnitudes?", "Option C states weight magnitudes increase uncontrollably; the new stem asks for this, making C correct."),
        "D": ("Which answer says the neuron's output becomes approximately linear?", "Option D states the output becomes approximately linear; the new stem asks for this, making D correct."),
    },
    14: {
        "A": ("Which benefit is enabling parallel computation across sequence positions?", "Option A states it allows parallel computation; the new stem asks for this, making A correct."),
        "B": ("Which answer claims that sharing parameters eliminates vanishing gradients through averaging?", "Option B states it eliminates vanishing gradients through parameter averaging; the new stem asks for this, making B correct."),
        "C": ("Which explanation emphasizes increased model capacity by expanding representational depth?", "Option C states it increases capacity by expanding depth; the new stem asks for this, making C correct."),
    },
    15: {
        "B": ("Which loss is described as Smooth L1 over embeddings?", "Option B is Smooth L1 over embeddings; the new stem asks for this, making B correct."),
        "C": ("Which option identifies hinge loss over tags as the training objective?", "Option C is hinge loss over tags; the new stem asks for this, making C correct."),
        "D": ("Which option describes binary cross-entropy computed per position?", "Option D is binary cross-entropy per position; the new stem asks for this, making D correct."),
    },
    16: {
        "A": ("Which scenario says both vocabulary size and sequence length decrease?", "Option A states both decrease; the new stem asks for this, making A correct."),
        "C": ("Which option claims that both vocabulary size and sequence length increase?", "Option C states both increase; the new stem asks for this, making C correct."),
        "D": ("Which description states vocabulary size decreases dramatically while sequence length becomes extremely long?", "Option D states vocabulary decreases and sequence length becomes extremely long; the new stem asks for this, making D correct."),
    },
    17: {
        "A": ("Which explanation emphasizes allocating separate parameters for each time step?", "Option A states allocating separate parameters per step; the new stem asks for this, making A correct."),
        "C": ("Which option claims that unrolling is done to remove weight sharing across sequence positions?", "Option C states unrolling removes weight sharing; the new stem asks for this, making C correct."),
        "D": ("Which answer focuses on increasing hidden state dimensional capacity?", "Option D states increasing hidden state capacity; the new stem asks for this, making D correct."),
    },
    18: {
        "A": ("Which option claims LSTMs work by freezing the recurrent matrix $U$?", "Option A states freezing the recurrent matrix U; the new stem asks for this, making A correct."),
        "C": ("Which explanation says LSTMs use convolution instead of recurrence?", "Option C states using convolution instead of recurrence; the new stem asks for this, making C correct."),
        "D": ("Which answer states that LSTMs remove nonlinearity between layers?", "Option D states removing nonlinearity between layers; the new stem asks for this, making D correct."),
    },
    19: {
        "B": ("Which architecture combines Word2Vec with a decoder RNN for this kind of task?", "Option B is Word2Vec + Decoder RNN; the new stem asks for this, making B correct."),
        "C": ("Which approach uses a Bag-of-Words representation with a Naive Bayes classifier?", "Option C is Bag-of-Words + Naive Bayes; the new stem asks for this, making C correct."),
        "D": ("Which model type is a Hidden Markov Model?", "Option D is Hidden Markov Models; the new stem asks for this, making D correct."),
    },
    20: {
        "A": ("Which explanation blames a misconfigured cross-entropy loss for this behavior?", "Option A states cross-entropy loss misconfigured; the new stem asks for this, making A correct."),
        "B": ("Which option points to the final Softmax layer using no temperature scaling as the cause?", "Option B states the final layer uses Softmax without temperature scaling; the new stem asks for this, making B correct."),
        "C": ("Which answer attributes the issue to an excessively high learning rate?", "Option C states learning rate too high; the new stem asks for this, making C correct."),
    },
    21: {
        "A": ("Which explanation blames dropout being disabled?", "Option A states dropout disabled; the new stem asks for this, making A correct."),
        "B": ("Which option points to the input data not being normalized?", "Option B states the input data has not been normalized; the new stem asks for this, making B correct."),
        "D": ("Which answer attributes the issue to learning rate being too high?", "Option D states learning rate too high; the new stem asks for this, making D correct."),
    },
    22: {
        "A": ("Which option describes biased gradient estimates but lower variance?", "Option A states biased estimates but lower variance; the new stem asks for this, making A correct."),
        "B": ("Which option describes deterministic updates with faster convergence?", "Option B states deterministic updates with faster convergence; the new stem asks for this, making B correct."),
        "D": ("Which option describes smaller parameter magnitudes?", "Option D states smaller parameter magnitudes; the new stem asks for this, making D correct."),
    },
    23: {
        "A": ("Which option says BPE removes infrequent words from the vocabulary?", "Option A states it removes infrequent words; the new stem asks for this, making A correct."),
        "B": ("Which option claims BPE increases vocabulary size?", "Option B states it increases vocabulary size; the new stem asks for this, making B correct."),
        "D": ("Which option says BPE converts tokens into fixed-length character blocks?", "Option D states it converts tokens into fixed-length character blocks; the new stem asks for this, making D correct."),
    },
    24: {
        "A": ("Which explanation attributes poor inference to cross-entropy over-penalizing rare tokens?", "Option A states cross-entropy over-penalizes rare tokens; the new stem asks for this, making A correct."),
        "C": ("Which explanation blames insufficient hidden state dimensionality for long sequences?", "Option C states hidden state dimensionality is insufficient; the new stem asks for this, making C correct."),
        "D": ("Which explanation attributes the behavior to the optimizer failing to converge?", "Option D states the optimizer fails to converge; the new stem asks for this, making D correct."),
    },
    25: {
        "A": ("Which component is the input embeddings?", "Option A is input embeddings; the new stem asks for this, making A correct."),
        "B": ("Which component is the output logits?", "Option B is output logits; the new stem asks for this, making B correct."),
        "D": ("Which component is the hidden state $h$?", "Option D is hidden state h; the new stem asks for this, making D correct."),
    },
    26: {
        "A": ("Which option states that their Euclidean distance must be maximal?", "Option A states Euclidean distance must be maximal; the new stem asks for this, making A correct."),
        "B": ("Which option states that the documents have different lengths?", "Option B states the documents have different lengths; the new stem asks for this, making B correct."),
        "C": ("Which option states that the documents are unrelated in meaning?", "Option C states the documents are unrelated in meaning; the new stem asks for this, making C correct."),
    },
    27: {
        "B": ("Which option says tokenization ensures every word has a single unchanging meaning?", "Option B states it ensures every word has a single unchanging meaning; the new stem asks for this, making B correct."),
        "C": ("Which option says tokenization compresses the sentence into a shorter representation?", "Option C states it compresses the sentence; the new stem asks for this, making C correct."),
        "D": ("Which option says tokenization removes grammatical ambiguity before training?", "Option D states it removes grammatical ambiguity; the new stem asks for this, making D correct."),
    },
    28: {
        "A": ("Which numerical value is $0.12$?", "Option A gives 0.12; the new stem asks for this value, making A correct."),
        "C": ("Which numerical value is $0.21$?", "Option C gives 0.21; the new stem asks for this value, making C correct."),
        "D": ("Which numerical value is $0.042$?", "Option D gives 0.042; the new stem asks for this value, making D correct."),
    },
    29: {
        "A": ("Which explanation says lower perplexity always indicates overfitting to training data?", "Option A states lower perplexity indicates overfitting; the new stem asks for this, making A correct."),
        "B": ("Which explanation says perplexity ignores normalization across token positions?", "Option B states perplexity ignores normalization; the new stem asks for this, making B correct."),
        "C": ("Which explanation says question answering requires larger vocabularies than modeling?", "Option C states QA requires larger vocabularies; the new stem asks for this, making C correct."),
    },
    30: {
        "A": ("Which explanation attributes the behavior to batch size being too small?", "Option A states batch size too small; the new stem asks for this, making A correct."),
        "B": ("Which explanation attributes the behavior to batch size being too large?", "Option B states batch size too large; the new stem asks for this, making B correct."),
        "C": ("Which explanation attributes the behavior to learning rate being too small?", "Option C states learning rate too small; the new stem asks for this, making C correct."),
    },
    31: {
        "A": ("Which numerical value is the perplexity $4.215$?", "Option A gives 4.215; the new stem asks for this, making A correct."),
        "B": ("Which numerical value is the perplexity $2.154$?", "Option B gives 2.154; the new stem asks for this, making B correct."),
        "C": ("Which numerical value is the perplexity $5.000$?", "Option C gives 5.000; the new stem asks for this, making C correct."),
    },
    32: {
        "B": ("Which statement says the state probabilities continue fluctuating without convergence?", "Option B states probabilities continue fluctuating; the new stem asks for this, making B correct."),
        "C": ("Which statement says the limiting distribution depends on the initial state?", "Option C states the limiting distribution depends on initial state; the new stem asks for this, making C correct."),
        "D": ("Which statement says the chain eventually remains permanently in one state?", "Option D states the chain remains permanently in one state; the new stem asks for this, making D correct."),
    },
    33: {
        "A": ("Which objective minimizes the squared Euclidean distance between embeddings of words in the same document?", "Option A describes minimizing squared Euclidean distance; the new stem asks for this, making A correct."),
        "C": ("Which objective maximizes cosine similarity between word pairs within a fixed window?", "Option C describes maximizing cosine similarity in a window; the new stem asks for this, making C correct."),
        "D": ("Which objective maximizes $\\log P(c \\mid w)$ using a full softmax over the vocabulary?", "Option D describes maximizing log P(c|w) with full softmax; the new stem asks for this, making D correct."),
    },
    34: {
        "A": ("Which option says ELMo represents words using character-level frequency features?", "Option A states character-level frequency features; the new stem asks for this, making A correct."),
        "B": ("Which option says ELMo learns embeddings solely from global co-occurrence statistics?", "Option B states it learns from global co-occurrence statistics; the new stem asks for this, making B correct."),
        "D": ("Which option says the method assigns a single fixed vector to each word type?", "Option D states a single fixed vector per word type (Word2Vec); the new stem asks for this, making D correct."),
    },
}


def build_perturbation_entry(q_idx: int, latex_stem: str, orig_sub: str, repl: str, target: str, reasoning: str) -> dict:
    start = 0
    end = len(orig_sub)
    return {
        "question_index": q_idx,
        "latex_stem_text": latex_stem,
        "original_substring": orig_sub,
        "replacement_substring": repl,
        "start_pos": start,
        "end_pos": end,
        "target_wrong_answer": target,
        "reasoning": reasoning,
    }


def main():
    out = {
        "docid": "SET_D",
        "domain": "computer_science",
        "academic_level": "undergraduate",
        "file_paths": {
            "latex_file": os.path.join(BASE, "SET_D.tex"),
            "pdf_file": os.path.join(BASE, "SET_D.pdf"),
        },
        "questions": [],
    }

    for i, (latex_stem, stem_plain, options, gold) in enumerate(QUESTIONS_DATA, start=1):
        q = {
            "question_number": i,
            "question_type": "MCQ",
            "stem_text": stem_plain,
            "options": options,
            "gold_answer": gold,
            "latex_stem_text": latex_stem,
            "perturbations": [],
        }
        wrong_options = [k for k in options if k != gold]
        pert_data = PERTURBATIONS.get(i, {})
        for opt in wrong_options:
            if opt not in pert_data:
                raise KeyError(f"Q{i}: missing perturbation for option {opt}")
            repl, reasoning = pert_data[opt]
            q["perturbations"].append(
                build_perturbation_entry(i, latex_stem, latex_stem, repl, opt, reasoning)
            )
        out["questions"].append(q)

    out_path = os.path.join(BASE, "manual_perturbations", "SET_D_perturbation.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
