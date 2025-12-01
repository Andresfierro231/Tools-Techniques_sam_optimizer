"""
data_handler_demo.py

Quick sanity check for data_handler.build_basic_dataset().

Run with:
    cd active_development
    python -m sam_tuner.data_handler_demo
"""

from sam_tuner.data_handler import build_basic_dataset, FEATURE_COLUMNS, ERROR_COLUMN, RUNTIME_COLUMN


def main():
    X, y_err, y_rt = build_basic_dataset()

    print("=== Data handler demo ===")
    print(f"Feature columns: {FEATURE_COLUMNS}")
    print(f"Error column   : {ERROR_COLUMN}")
    print(f"Runtime column : {RUNTIME_COLUMN}")
    print()
    print(f"X shape       : {X.shape}")
    print(f"y_error shape : {y_err.shape}")
    print(f"y_runtime shape: {y_rt.shape}")
    print()
    print("First few rows of X:")
    print(X.head())

    print("\nFirst few error values:")
    print(y_err.head())

    print("\nFirst few runtime values:")
    print(y_rt.head())


if __name__ == "__main__":
    main()
