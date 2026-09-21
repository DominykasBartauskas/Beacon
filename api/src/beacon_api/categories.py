import re

AI_RESEARCH = "AI Research"
MODELS_RELEASES = "Models & Releases"
AI_ENGINEERING = "AI Engineering"
SOFTWARE_DEVELOPMENT = "Software Development"
TOOLS_PLATFORMS = "Tools & Platforms"
AI_PRODUCTS = "AI Products & Applications"
SAFETY_SECURITY = "Safety & Security"

CATEGORIES = (
    AI_RESEARCH,
    MODELS_RELEASES,
    AI_ENGINEERING,
    SOFTWARE_DEVELOPMENT,
    TOOLS_PLATFORMS,
    AI_PRODUCTS,
    SAFETY_SECURITY,
)

# Ordered most specific first: a jailbreak paper is Safety, not Research, and a
# model card is a Release, not a Product. Ties break towards the earlier entry.
RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        SAFETY_SECURITY,
        (
            "jailbreak", "red team", "red-team", "alignment", "safety", "guardrail",
            "adversarial", "prompt injection", "vulnerability", "exploit", "cve",
            "misuse", "harmful", "interpretability", "eu ai act", "regulation",
            "governance", "privacy", "watermark", "deepfake",
        ),
    ),
    (
        MODELS_RELEASES,
        (
            # Deliberately not "release"/"version": a library release is Tools,
            # not a model release, and only the source knows which it publishes.
            "announcing", "introducing", "open-weight", "open weights",
            "checkpoint", "model card", "pretrained model", "base model",
            "instruct model", "fine-tune", "finetuned", "quantized", "distilled",
            "sota", "state-of-the-art",
        ),
    ),
    (
        AI_ENGINEERING,
        (
            "prompt", "prompting", "rag", "retrieval-augmented", "evaluation", "eval",
            "evals", "benchmark", "benchmarking", "fine-tuning", "inference",
            "serving", "latency", "throughput", "context window", "embedding",
            "vector database", "agent", "agents", "agentic", "tool use", "mcp",
            "observability", "token", "tokens",
        ),
    ),
    (
        TOOLS_PLATFORMS,
        (
            "framework", "library", "sdk", "toolkit", "cli", "ide", "plugin",
            "extension", "platform", "infrastructure", "kubernetes", "docker",
            "compiler", "runtime", "database", "api", "open source", "open-source",
            "github", "package", "dependency",
        ),
    ),
    (
        AI_PRODUCTS,
        (
            "product", "app", "assistant", "copilot", "chatbot", "customer",
            "enterprise", "startup", "pricing", "subscription", "users", "adoption",
            "workflow", "integration", "feature",
        ),
    ),
    (
        SOFTWARE_DEVELOPMENT,
        (
            "code", "coding", "programming", "developer", "engineering", "refactor",
            "debugging", "testing", "test suite", "pull request", "code review",
            "typescript", "python", "rust", "golang", "javascript", "compiler bug",
        ),
    ),
    (
        AI_RESEARCH,
        (
            "we propose", "we introduce", "we present", "paper", "study", "dataset",
            "training", "pretraining", "architecture", "transformer", "diffusion",
            "reinforcement learning", "neural", "scaling law", "empirical",
            "experiments", "theoretical", "novel",
        ),
    ),
)

_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = tuple(
    (category, tuple(re.compile(rf"(?<!\w){re.escape(term)}(?!\w)") for term in terms))
    for category, terms in RULES
)


def classify(title: str, summary: str = "", *, default: str) -> str:
    """Pick the first category in RULES order whose terms appear in the text.

    Order is priority: a jailbreak paper is Safety before it is Research. Match
    counting was the alternative, but generic words ("study", "neural") then
    outvoted specific ones, so a paper on adversarial attacks read as Research.

    The title decides on its own when it matches anything, since it describes
    the item; a summary often just mentions things in passing. With no match at
    all the source's own category wins, keeping a targeted feed in its lane.
    """
    for haystack in (title.lower(), summary.lower()):
        if not haystack:
            continue
        for category, patterns in _PATTERNS:
            if any(pattern.search(haystack) for pattern in patterns):
                return category
    return default
