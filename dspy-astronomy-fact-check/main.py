"""Run the fact-checker uncompiled, compile it with BootstrapFewShot, run it again."""

import pathlib

import dotenv
import dspy

import factcheck

dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

MODEL = "openai/gpt-4o-mini"


def score(program: dspy.Module, rows: list[dict]) -> int:
    handbook = factcheck.load_handbook()
    passed = 0
    for row in rows:
        pred = program(handbook=handbook, claim=row["claim"])
        ok = factcheck.check_answer(pred.verdict, pred.evidence, row["verdict"], row["passage"])
        passed += ok
        print(f"  {'ok  ' if ok else 'FAIL'} {row['claim']}  ->  {pred.verdict!r} / {pred.evidence!r}")
    return passed


def main() -> None:
    dspy.configure(lm=dspy.LM(MODEL, cache=False))
    test = factcheck.load_claims("test")
    uncompiled = factcheck.build_program()
    print("Uncompiled:")
    before = score(uncompiled, test)

    optimizer = dspy.BootstrapFewShot(
        metric=factcheck.metric, max_bootstrapped_demos=4, max_labeled_demos=4, max_rounds=1
    )
    compiled = optimizer.compile(
        uncompiled, trainset=factcheck.to_examples(factcheck.load_claims("train"))
    )
    print("Compiled:")
    after = score(compiled, test)
    print(f"\nexact-format pass: uncompiled {before}/{len(test)}, compiled {after}/{len(test)}")


if __name__ == "__main__":
    main()
