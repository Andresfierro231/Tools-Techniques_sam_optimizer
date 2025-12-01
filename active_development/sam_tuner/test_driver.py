"""
test_driver.py

Quick sanity test for run_sam_case + runtime_logger.

Run with:
    cd active_development
    python -m sam_opt.test_driver
"""

from .run_launcher import run_sam_case


def main():
    # Adjust hyperparams as needed (must make sense for your templates)
    hyperparams = {
        "node_multiplier": 6,
        "order": 2,
        # "htc": 1000.0,
    }

    result = run_sam_case(
        case_name="jsalt1",
        template_name="jsalt1.i",
        hyperparams=hyperparams,
    )

    print("Run summary:")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()