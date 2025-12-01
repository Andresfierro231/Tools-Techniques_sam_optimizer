"""
quick_sweep.py

Minimal multi-run driver that uses sam_tuner.run_sam_case
to sweep node_multiplier and order across jsalt templates.

Run with:
    cd active_development
    python -m sam_tuner.quick_sweep
"""

from sam_tuner.run_launcher import run_sam_case


# You can tweak these lists freely.
TEMPLATES = ["jsalt1.i", "jsalt2.i", "jsalt3.i", "jsalt4.i"]

NODE_MULT_LIST = [1, 2, 4, 6, 8, 12, 16, 24]  # adjust as you like
ORDERS = [1, 2]  # 1 = FIRST, 2 = SECOND


def main():
    run_count = 0
    for order in ORDERS:
        for template_name in TEMPLATES:
            # case_name can be equal to the template stem (jsalt1, jsalt2, ...)
            case_name = template_name.split(".")[0]

            for nm in NODE_MULT_LIST:
                hyperparams = {
                    "node_multiplier": nm,
                    "order": order,
                    # "htc": 1000.0,  # you can add this later
                }

                print(
                    f"\n=== Running {case_name} | order={order} | node_multiplier={nm} ==="
                )
                result = run_sam_case(
                    case_name=case_name,
                    template_name=template_name,
                    hyperparams=hyperparams,
                    # timeout_sec=None  # use default from config
                )

                run_count += 1
                print("Summary:")
                for k, v in result.items():
                    print(f"  {k}: {v}")

    print(f"\nFinished sweep. Total runs: {run_count}")


if __name__ == "__main__":
    main()
