def run_with_retries(parserFun, genratorFun, max_retries=3):
    attempts = 0
    while attempts < max_retries:
        try:
            # Attempt to run the function
            fucToRetry
            text = geratorFun()
            result = parserFun(text)
            print("Function executed successfully!")
            return result  # If successful, return the result
        except Exception as e:
            # Handle the exception (print or log it) and retry
            attempts += 1
            print(f"Attempt {attempts} failed: {e}")
            if attempts == max_retries:
                print("Max retries reached. Giving up.")
                raise  # Re-raise the last exception after max retries
