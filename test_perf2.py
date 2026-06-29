import sys, os, traceback
sys.path.insert(0, os.path.abspath('dashboard'))
from app import app
app.testing = True

def run():
    with app.test_request_context('/performance'):
        try:
            print("Running wrapped performance()")
            app.view_functions['performance'].__wrapped__()
            print("Finished successfully")
        except Exception as e:
            traceback.print_exc()

if __name__ == '__main__':
    run()
