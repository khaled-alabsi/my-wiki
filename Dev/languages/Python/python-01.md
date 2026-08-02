Here is a detailed explanation of each NumPy function, including at least two examples for each, and some additional commonly used functions.

### NumPy Functions

1. **arange**
   - Usage: `np.arange([start, ]stop, [step, ]dtype=None)`
   - Explanation: Creates an array with evenly spaced values within a given interval. The interval includes the start but excludes the stop.
   - Example 1 Input: `np.arange(0, 10, 2)`
   - Example 1 Expected Output: `array([0, 2, 4, 6, 8])`
     - Here, an array from 0 to 8 (exclusive of 10) is created with a step size of 2.
   - Example 2 Input: `np.arange(1.0, 5.0, 0.5)`
   - Example 2 Expected Output: `array([1. , 1.5, 2. , 2.5, 3. , 3.5, 4. , 4.5])`
     - Here, an array from 1.0 to 4.5 (exclusive of 5.0) is created with a step size of 0.5.

2. **array**
   - Usage: `np.array(object, dtype=None, copy=True, order='K', subok=False, ndmin=0)`
   - Explanation: Creates an array from any object exposing the array interface, such as lists or tuples.
   - Example 1 Input: `np.array([1, 2, 3, 4])`
   - Example 1 Expected Output: `array([1, 2, 3, 4])` 
     - Converts a list to a NumPy array.
   - Example 2 Input: `np.array([(1, 2), (3, 4)], dtype=complex)`
   - Example 2 Expected Output: `array([[1.+0.j, 2.+0.j], [3.+0.j, 4.+0.j]])`
     - Converts a list of tuples to a NumPy array with complex data type.

3. **hstack**
   - Usage: `np.hstack(tup)`
   - Explanation: Stacks arrays in sequence horizontally (column wise).
   - Example 1 Input: `np.hstack(([1, 2], [3, 4]))`
   - Example 1 Expected Output: `array([1, 2, 3, 4])`
     - Concatenates two 1-dimensional arrays into one.
   - Example 2 Input: `np.hstack(([[1, 2], [3, 4]], [[5, 6], [7, 8]]))`
   - Example 2 Expected Output: `array([[1, 2, 5, 6], [3, 4, 7, 8]])`
     - Concatenates two 2-dimensional arrays column-wise.

4. **interp**
   - Usage: `np.interp(x, xp, fp, left=None, right=None, period=None)`
   - Explanation: One-dimensional linear interpolation.
   - Example 1 Input: `np.interp(5, [0, 10], [0, 100])`
   - Example 1 Expected Output: `50.0`
     - Interpolates the value 5 within the interval [0, 10] to a corresponding value within [0, 100].
   - Example 2 Input: `np.interp([2.5, 5, 7.5], [0, 10], [0, 100])`
   - Example 2 Expected Output: `array([25., 50., 75.])`
     - Interpolates multiple values within the given intervals.

5. **linspace**
   - Usage: `np.linspace(start, stop, num=50, endpoint=True, retstep=False, dtype=None, axis=0)`
   - Explanation: Returns evenly spaced numbers over a specified interval.
   - Example 1 Input: `np.linspace(0, 10, 5)`
   - Example 1 Expected Output: `array([ 0.,  2.5,  5.,  7.5, 10.])`
     - Generates 5 evenly spaced values between 0 and 10.
   - Example 2 Input: `np.linspace(0, 1, 5, endpoint=False)`
   - Example 2 Expected Output: `array([0. , 0.2, 0.4, 0.6, 0.8])`
     - Generates 5 evenly spaced values between 0 and 1, not including the endpoint 1.

6. **mean**
   - Usage: `np.mean(a, axis=None, dtype=None, out=None, keepdims=<no value>, *, where=<no value>)`
   - Explanation: Computes the arithmetic mean along the specified axis.
   - Example 1 Input: `np.mean([1, 2, 3, 4])`
   - Example 1 Expected Output: `2.5`
     - Calculates the mean of the array.
   - Example 2 Input: `np.mean([[1, 2, 3], [4, 5, 6]], axis=0)`
   - Example 2 Expected Output: `array([2.5, 3.5, 4.5])`
     - Calculates the mean along the columns of a 2-dimensional array.

7. **roll**
   - Usage: `np.roll(a, shift, axis=None)`
   - Explanation: Rolls array elements along a specified axis.
   - Example 1 Input: `np.roll([1, 2, 3, 4], 2)`
   - Example 1 Expected Output: `array([3, 4, 1, 2])`
     - Rolls elements of the array to the right by 2 positions.
   - Example 2 Input: `np.roll([[1, 2], [3, 4]], 1, axis=0)`
   - Example 2 Expected Output: `array([[3, 4], [1, 2]])`
     - Rolls elements of a 2-dimensional array along the rows.

8. **sin**
   - Usage: `np.sin(x, /, out=None, *, where=True, casting='same_kind', order='K', dtype=None, subok=True[, signature, extobj])`
   - Explanation: Trigonometric sine, element-wise.
   - Example 1 Input: `np.sin(np.pi / 2)`
   - Example 1 Expected Output: `1.0`
     - Computes the sine of π/2 radians.
   - Example 2 Input: `np.sin([0, np.pi / 2, np.pi])`
   - Example 2 Expected Output: `array([0.0000000e+00, 1.0000000e+00, 1.2246468e-16])`
     - Computes the sine of multiple angles, resulting in an array of sine values.

9. **sort**
   - Usage: `np.sort(a, axis=-1, kind=None, order=None)`
   - Explanation: Returns a sorted copy of an array.
   - Example 1 Input: `np.sort([3, 1, 2])`
   - Example 1 Expected Output: `array([1, 2, 3])`
     - Sorts the array in ascending order.
   - Example 2 Input: `np.sort([[1, 4], [3, 1]], axis=1)`
   - Example 2 Expected Output: `array([[1, 4], [1, 3]])`
     - Sorts the elements of each row in ascending order.

10. **sqrt**
    - Usage: `np.sqrt(x, /, out=None, *, where=True, casting='same_kind', order='K', dtype=None, subok=True[, signature, extobj])`
    - Explanation: Computes the non-negative square-root of an array, element-wise.
    - Example 1 Input: `np.sqrt(4)`
    - Example 1 Expected Output: `2.0`
      - Computes the square root of 4.
    - Example 2 Input: `np.sqrt([1, 4, 9])`
    - Example 2 Expected Output: `array([1., 2., 3.])`
      - Computes the square roots of the elements in the array.

11. **std**
    - Usage: `np.std(a, axis=None, dtype=None, out=None, ddof=0, keepdims=<no value>, *, where=<no value>)`
    - Explanation: Computes the standard deviation along the specified axis.
    - Example 1 Input: `np.std([1, 2, 3, 4])`
    - Example 1 Expected Output: `1.118033988749895`
      - Calculates the standard deviation of the array.
    - Example 2 Input: `np.std([[1, 2, 3], [4, 5, 6]], axis=0)`
    - Example 2 Expected Output: `array([1.5, 1.5, 1.5])`
      - Calculates the standard deviation along the columns of a 2-dimensional array.

12. **var**
    - Usage: `np.var(a, axis=None, dtype=None, out=None, ddof=0, keepdims=<no value>, *, where=<no value>)`
    - Explanation: Computes the variance along the specified axis.
    - Example 1 Input: `np

.var([1, 2, 3, 4])`
    - Example 1 Expected Output: `1.25`
      - Calculates the variance of the array.
    - Example 2 Input: `np.var([[1, 2, 3], [4, 5, 6]], axis=1)`
    - Example 2 Expected Output: `array([0.66666667, 0.66666667])`
      - Calculates the variance along the rows of a 2-dimensional array.

13. **where**
    - Usage: `np.where(condition, [x, y, ]/)`
    - Explanation: Return elements chosen from `x` or `y` depending on `condition`.
    - Example 1 Input: `np.where([True, False, True], [1, 2, 3], [4, 5, 6])`
    - Example 1 Expected Output: `array([1, 5, 3])`
      - Selects elements from `x` or `y` based on the condition.
    - Example 2 Input: `np.where(np.array([1, 2, 3, 4]) > 2, 'yes', 'no')`
    - Example 2 Expected Output: `array(['no', 'no', 'yes', 'yes'], dtype='<U3')`
      - Returns 'yes' if the condition is met, 'no' otherwise.

14. **ones**
    - Usage: `np.ones(shape, dtype=None, order='C')`
    - Explanation: Return a new array of given shape and type, filled with ones.
    - Example 1 Input: `np.ones((2, 3))`
    - Example 1 Expected Output: `array([[1., 1., 1.], [1., 1., 1.]])`
      - Creates a 2x3 array filled with ones.
    - Example 2 Input: `np.ones(5)`
    - Example 2 Expected Output: `array([1., 1., 1., 1., 1.])`
      - Creates a 1-dimensional array of length 5 filled with ones.

15. **zeros**
    - Usage: `np.zeros(shape, dtype=float, order='C')`
    - Explanation: Return a new array of given shape and type, filled with zeros.
    - Example 1 Input: `np.zeros((3, 2))`
    - Example 1 Expected Output: `array([[0., 0.], [0., 0.], [0., 0.]])`
      - Creates a 3x2 array filled with zeros.
    - Example 2 Input: `np.zeros(4)`
    - Example 2 Expected Output: `array([0., 0., 0., 0.])`
      - Creates a 1-dimensional array of length 4 filled with zeros.

16. **random.rand**
    - Usage: `np.random.rand(d0, d1, ..., dn)`
    - Explanation: Creates an array of the given shape and populates it with random samples from a uniform distribution over [0, 1).
    - Example 1 Input: `np.random.rand(2, 3)`
    - Example 1 Expected Output: 
      ```
      array([[0.5488135 , 0.71518937, 0.60276338],
             [0.54488318, 0.4236548 , 0.64589411]])
      ```
      - Creates a 2x3 array of random numbers.
    - Example 2 Input: `np.random.rand(4)`
    - Example 2 Expected Output: 
      ```
      array([0.5488135 , 0.71518937, 0.60276338, 0.54488318])
      ```
      - Creates a 1-dimensional array of 4 random numbers.

17. **random.randn**
    - Usage: `np.random.randn(d0, d1, ..., dn)`
    - Explanation: Creates an array of the given shape and populates it with random samples from a standard normal distribution.
    - Example 1 Input: `np.random.randn(2, 3)`
    - Example 1 Expected Output: 
      ```
      array([[ 0.83423142, -0.34734514,  0.35122995],
             [ 0.26723496, -0.12334634, -0.54707337]])
      ```
      - Creates a 2x3 array of random numbers from a standard normal distribution.
    - Example 2 Input: `np.random.randn(4)`
    - Example 2 Expected Output: 
      ```
      array([ 0.83423142, -0.34734514,  0.35122995,  0.26723496])
      ```
      - Creates a 1-dimensional array of 4 random numbers from a standard normal distribution.

18. **dot**
    - Usage: `np.dot(a, b, out=None)`
    - Explanation: Dot product of two arrays.
    - Example 1 Input: `np.dot([1, 2], [3, 4])`
    - Example 1 Expected Output: `11`
      - Computes the dot product of two 1-dimensional arrays.
    - Example 2 Input: `np.dot([[1, 2], [3, 4]], [[5, 6], [7, 8]])`
    - Example 2 Expected Output: 
      ```
      array([[19, 22],
             [43, 50]])
      ```
      - Computes the dot product of two 2-dimensional arrays.

19. **max**
    - Usage: `np.max(a, axis=None, out=None, keepdims=<no value>, initial=<no value>, where=<no value>)`
    - Explanation: Return the maximum of an array or maximum along an axis.
    - Example 1 Input: `np.max([1, 2, 3, 4])`
    - Example 1 Expected Output: `4`
      - Finds the maximum value in the array.
    - Example 2 Input: `np.max([[1, 2], [3, 4]], axis=0)`
    - Example 2 Expected Output: `array([3, 4])`
      - Finds the maximum values along the columns of a 2-dimensional array.

20. **min**
    - Usage: `np.min(a, axis=None, out=None, keepdims=<no value>, initial=<no value>, where=<no value>)`
    - Explanation: Return the minimum of an array or minimum along an axis.
    - Example 1 Input: `np.min([1, 2, 3, 4])`
    - Example 1 Expected Output: `1`
      - Finds the minimum value in the array.
    - Example 2 Input: `np.min([[1, 2], [3, 4]], axis=1)`
    - Example 2 Expected Output: `array([1, 3])`
      - Finds the minimum values along the rows of a 2-dimensional array.


Here is a detailed explanation of each pandas function, including at least two examples for each, and some additional commonly used functions.

### pandas Functions

1. **DataFrame**
   - Usage: `pd.DataFrame(data=None, index=None, columns=None, dtype=None, copy=False)`
   - Explanation: Creates a DataFrame, which is a 2-dimensional labeled data structure with columns of potentially different types.
   - Example 1 Input: `pd.DataFrame({'a': [1, 2], 'b': [3, 4]})`
   - Example 1 Expected Output:
     ```
        a  b
     0  1  3
     1  2  4
     ```
     - Creates a DataFrame from a dictionary with columns 'a' and 'b', where each column has two values.
   - Example 2 Input: `pd.DataFrame([[1, 2], [3, 4]], columns=['a', 'b'])`
   - Example 2 Expected Output:
     ```
        a  b
     0  1  2
     1  3  4
     ```
     - Creates a DataFrame from a list of lists with specified column names.

2. **read_csv**
   - Usage: `pd.read_csv(filepath_or_buffer, sep=',', delimiter=None, header='infer', names=None, index_col=None, usecols=None, ...)`
   - Explanation: Reads a comma-separated values (CSV) file into a DataFrame.
   - Example 1 Input: `pd.read_csv('file.csv')`
   - Example 1 Expected Output: DataFrame with contents of `file.csv`
     - Reads the CSV file named 'file.csv' into a DataFrame.
   - Example 2 Input: `pd.read_csv('file.csv', index_col=0)`
   - Example 2 Expected Output: DataFrame with the first column of `file.csv` as the index
     - Reads the CSV file and sets the first column as the index of the DataFrame.

3. **head**
   - Usage: `DataFrame.head(n=5)`
   - Explanation: Returns the first n rows of the DataFrame.
   - Example 1 Input: `df.head(3)`
   - Example 1 Expected Output:
     ```
        a  b
     0  1  3
     1  2  4
     2  3  5
     ```
     - Returns the first 3 rows of the DataFrame.
   - Example 2 Input: `df.head()`
   - Example 2 Expected Output:
     ```
        a  b
     0  1  3
     1  2  4
     2  3  5
     3  4  6
     4  5  7
     ```
     - Returns the first 5 rows of the DataFrame (default).

4. **tail**
   - Usage: `DataFrame.tail(n=5)`
   - Explanation: Returns the last n rows of the DataFrame.
   - Example 1 Input: `df.tail(2)`
   - Example 1 Expected Output:
     ```
        a  b
     3  4  6
     4  5  7
     ```
     - Returns the last 2 rows of the DataFrame.
   - Example 2 Input: `df.tail()`
   - Example 2 Expected Output:
     ```
        a  b
     0  1  3
     1  2  4
     2  3  5
     3  4  6
     4  5  7
     ```
     - Returns the last 5 rows of the DataFrame (default).

5. **describe**
   - Usage: `DataFrame.describe(percentiles=None, include=None, exclude=None)`
   - Explanation: Generates descriptive statistics that summarize the central tendency, dispersion, and shape of a dataset’s distribution, excluding NaN values.
   - Example 1 Input: `df.describe()`
   - Example 1 Expected Output:
     ```
                a         b
     count  5.000000  5.000000
     mean   3.000000  5.000000
     std    1.581139  1.581139
     min    1.000000  3.000000
     25%    2.000000  4.000000
     50%    3.000000  5.000000
     75%    4.000000  6.000000
     max    5.000000  7.000000
     ```
     - Provides summary statistics of the DataFrame columns 'a' and 'b'.
   - Example 2 Input: `df.describe(include='all')`
   - Example 2 Expected Output: Summary statistics including non-numeric data if present.
     ```
                a         b
     count  5.000000  5.000000
     mean   3.000000  5.000000
     std    1.581139  1.581139
     min    1.000000  3.000000
     25%    2.000000  4.000000
     50%    3.000000  5.000000
     75%    4.000000  6.000000
     max    5.000000  7.000000
     ```

6. **info**
   - Usage: `DataFrame.info(verbose=None, buf=None, max_cols=None, memory_usage=None, null_counts=None)`
   - Explanation: Prints a concise summary of a DataFrame.
   - Example 1 Input: `df.info()`
   - Example 1 Expected Output:
     ```
     <class 'pandas.core.frame.DataFrame'>
     RangeIndex: 5 entries, 0 to 4
     Data columns (total 2 columns):
     #   Column  Non-Null Count  Dtype
     ---  ------  --------------  -----
     0   a       5 non-null      int64
     1   b       5 non-null      int64
     dtypes: int64(2)
     memory usage: 208.0 bytes
     ```
     - Provides a concise summary of the DataFrame, including the number of non-null entries and the data types of each column.
   - Example 2 Input: `df.info(memory_usage='deep')`
   - Example 2 Expected Output: Same as above, but with deep memory usage analysis.

7. **iloc**
   - Usage: `DataFrame.iloc[row_indexer, column_indexer]`
   - Explanation: Purely integer-location based indexing for selection by position.
   - Example 1 Input: `df.iloc[0]`
   - Example 1 Expected Output:
     ```
     a    1
     b    3
     Name: 0, dtype: int64
     ```
     - Selects the first row of the DataFrame.
   - Example 2 Input: `df.iloc[:, 1]`
   - Example 2 Expected Output:
     ```
     0    3
     1    4
     2    5
     3    6
     4    7
     Name: b, dtype: int64
     ```
     - Selects the second column of the DataFrame.

8. **loc**
   - Usage: `DataFrame.loc[row_indexer, column_indexer]`
   - Explanation: Access a group of rows and columns by labels or a boolean array.
   - Example 1 Input: `df.loc[0]`
   - Example 1 Expected Output:
     ```
     a    1
     b    3
     Name: 0, dtype: int64
     ```
     - Selects the first row of the DataFrame using label-based indexing.
   - Example 2 Input: `df.loc[:, 'a']`
   - Example 2 Expected Output:
     ```
     0    1
     1    2
     2    3
     3    4
     4    5
     Name: a, dtype: int64
     ```
     - Selects the 'a' column of the DataFrame using label-based indexing.

9. **merge**
   - Usage: `pd.merge(left, right, how='inner', on=None, left_on=None, right_on=None, left_index=False, right_index=False, ...)`
   - Explanation: Merge DataFrame or named Series objects with a database-style join.
   - Example 1 Input:
     ```python
     df1 = pd.DataFrame({'key': ['A', 'B', 'C'], 'value': [1, 2, 3]})
     df2 = pd.DataFrame({'key': ['A', 'B', 'D'], 'value': [4, 5, 6]})
     pd.merge(df1, df2, on='key')
     ```
   - Example 1 Expected Output:
     ```
       key  value_x  value_y
     0   A        1        4
     1   B        2        5
     ```
     - Merges df1 and df2 on the 'key' column, performing an inner join.
   - Example 2 Input:
     ```python
     pd.merge(df

1, df2, on='key', how='outer')
     ```
   - Example 2 Expected Output:
     ```
       key  value_x  value_y
     0   A      1.0      4.0
     1   B      2.0      5.0
     2   C      3.0      NaN
     3   D      NaN      6.0
     ```
     - Merges df1 and df2 on the 'key' column, performing an outer join.

10. **groupby**
    - Usage: `DataFrame.groupby(by=None, axis=0, level=None, as_index=True, sort=True, group_keys=True, squeeze=False, observed=False, dropna=True)`
    - Explanation: Group DataFrame using a mapper or by a Series of columns.
    - Example 1 Input:
      ```python
      df = pd.DataFrame({'A': ['foo', 'bar', 'foo', 'bar'], 'B': [1, 2, 3, 4]})
      df.groupby('A').sum()
      ```
    - Example 1 Expected Output:
      ```
           B
      A
      bar  6
      foo  4
      ```
      - Groups the DataFrame by column 'A' and calculates the sum for each group.
    - Example 2 Input:
      ```python
      df.groupby('A').mean()
      ```
    - Example 2 Expected Output:
      ```
           B
      A
      bar  3.0
      foo  2.0
      ```
      - Groups the DataFrame by column 'A' and calculates the mean for each group.

11. **pivot_table**
    - Usage: `pd.pivot_table(data, values=None, index=None, columns=None, aggfunc='mean', fill_value=None, margins=False, dropna=True, margins_name='All')`
    - Explanation: Creates a spreadsheet-style pivot table as a DataFrame.
    - Example 1 Input:
      ```python
      df = pd.DataFrame({'A': ['foo', 'bar', 'foo', 'bar'], 'B': ['one', 'one', 'two', 'two'], 'C': [1, 2, 3, 4]})
      pd.pivot_table(df, values='C', index=['A', 'B'], aggfunc=np.sum)
      ```
    - Example 1 Expected Output:
      ```
                 C
      A   B
      bar one  2
          two  4
      foo one  1
          two  3
      ```
      - Creates a pivot table that sums the values of 'C' for each combination of 'A' and 'B'.
    - Example 2 Input:
      ```python
      pd.pivot_table(df, values='C', index='A', columns='B', aggfunc=np.mean)
      ```
    - Example 2 Expected Output:
      ```
      B    one  two
      A
      bar  2.0  4.0
      foo  1.0  3.0
      ```
      - Creates a pivot table that shows the mean of 'C' for each combination of 'A' and 'B'.

12. **apply**
    - Usage: `DataFrame.apply(func, axis=0, raw=False, result_type=None, args=(), **kwds)`
    - Explanation: Applies a function along an axis of the DataFrame.
    - Example 1 Input:
      ```python
      df = pd.DataFrame({'A': [1, 2, 3], 'B': [10, 20, 30]})
      df.apply(np.square)
      ```
    - Example 1 Expected Output:
      ```
         A    B
      0  1  100
      1  4  400
      2  9  900
      ```
      - Applies the numpy square function to each element of the DataFrame.
    - Example 2 Input:
      ```python
      df.apply(lambda x: x + 1)
      ```
    - Example 2 Expected Output:
      ```
         A   B
      0  2  11
      1  3  21
      2  4  31
      ```
      - Applies a lambda function that adds 1 to each element of the DataFrame.

13. **concat**
    - Usage: `pd.concat(objs, axis=0, join='outer', ignore_index=False, keys=None, levels=None, names=None, verify_integrity=False, sort=False, copy=True)`
    - Explanation: Concatenates pandas objects along a particular axis with optional set logic along the other axes.
    - Example 1 Input:
      ```python
      df1 = pd.DataFrame({'A': ['A0', 'A1', 'A2'], 'B': ['B0', 'B1', 'B2']})
      df2 = pd.DataFrame({'A': ['A3', 'A4', 'A5'], 'B': ['B3', 'B4', 'B5']})
      pd.concat([df1, df2])
      ```
    - Example 1 Expected Output:
      ```
          A   B
      0  A0  B0
      1  A1  B1
      2  A2  B2
      0  A3  B3
      1  A4  B4
      2  A5  B5
      ```
      - Concatenates df1 and df2 along the rows.
    - Example 2 Input:
      ```python
      pd.concat([df1, df2], axis=1)
      ```
    - Example 2 Expected Output:
      ```
          A   B   A   B
      0  A0  B0  A3  B3
      1  A1  B1  A4  B4
      2  A2  B2  A5  B5
      ```
      - Concatenates df1 and df2 along the columns.

14. **drop**
    - Usage: `DataFrame.drop(labels=None, axis=0, index=None, columns=None, level=None, inplace=False, errors='raise')`
    - Explanation: Drops specified labels from rows or columns.
    - Example 1 Input:
      ```python
      df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
      df.drop(['A'], axis=1)
      ```
    - Example 1 Expected Output:
      ```
         B
      0  4
      1  5
      2  6
      ```
      - Drops the 'A' column from the DataFrame.
    - Example 2 Input:
      ```python
      df.drop([0])
      ```
    - Example 2 Expected Output:
      ```
         A  B
      1  2  5
      2  3  6
      ```
      - Drops the first row from the DataFrame.

15. **pivot**
    - Usage: `DataFrame.pivot(index=None, columns=None, values=None)`
    - Explanation: Reshapes data (produces a 'pivot' table) based on column values. Uses unique values from specified index/columns to form axes of the resulting DataFrame.
    - Example 1 Input:
      ```python
      df = pd.DataFrame({'A': ['foo', 'foo', 'bar', 'bar'],
                         'B': ['one', 'two', 'one', 'two'],
                         'C': [1, 3, 2, 4]})
      df.pivot(index='A', columns='B', values='C')
      ```
    - Example 1 Expected Output:
      ```
      B    one  two
      A
      bar  2.0  4.0
      foo  1.0  3.0
      ```
      - Reshapes the DataFrame by pivoting around 'A' and 'B' columns, using 'C' values.
    - Example 2 Input:
      ```python
      df.pivot(index='B', columns='A', values='C')
      ```
    - Example 2 Expected Output:
      ```
      A    bar  foo
      B
      one   2    1
      two   4    3
      ```
      - Reshapes the DataFrame by pivoting around 'B' and 'A' columns, using 'C' values.

Sure, here is a detailed explanation of each Matplotlib function, including at least two examples for each, and some additional commonly used functions.

### Matplotlib Functions

1. **figure**
   - Usage: `plt.figure(num=None, figsize=None, dpi=None, facecolor=None, edgecolor=None, frameon=True, FigureClass=<class 'matplotlib.figure.Figure'>, **kwargs)`
   - Explanation: Creates a new figure, which is a container for plots.
   - Example 1 Input: `plt.figure(figsize=(8, 6))`
   - Example 1 Expected Output: A new figure with a size of 8x6 inches.
     - Creates a figure of size 8x6 inches where subsequent plots will be drawn.
   - Example 2 Input: `plt.figure(num=2, dpi=100)`
   - Example 2 Expected Output: A new figure with an identifier of 2 and resolution of 100 dots per inch.
     - Creates a new figure with specific ID and resolution.

2. **plot**
   - Usage: `plt.plot(*args, scalex=True, scaley=True, data=None, **kwargs)`
   - Explanation: Plots y versus x as lines and/or markers.
   - Example 1 Input: `plt.plot([1, 2, 3], [4, 5, 6])`
   - Example 1 Expected Output: A line plot of points (1,4), (2,5), (3,6).
     - Plots a simple line graph with x-values [1, 2, 3] and y-values [4, 5, 6].
   - Example 2 Input: `plt.plot([1, 2, 3], [4, 5, 6], 'ro-')`
   - Example 2 Expected Output: A red line plot with circle markers.
     - Plots a line graph with x-values [1, 2, 3] and y-values [4, 5, 6] with red circles connected by lines.

3. **show**
   - Usage: `plt.show(*args, **kwargs)`
   - Explanation: Displays all open figures.
   - Example 1 Input: `plt.show()`
   - Example 1 Expected Output: Display of all figures created.
     - Displays the plot(s) created.
   - Example 2 Input:
     ```python
     plt.plot([1, 2, 3], [4, 5, 6])
     plt.show()
     ```
   - Example 2 Expected Output: A line plot is displayed in a window.
     - Creates and shows a plot of the given data.

4. **hist**
   - Usage: `plt.hist(x, bins=None, range=None, density=False, weights=None, cumulative=False, ...`
   - Explanation: Plots a histogram.
   - Example 1 Input: `plt.hist([1, 2, 2, 3], bins=3)`
   - Example 1 Expected Output: A histogram with 3 bins.
     - Plots a histogram of the data with 3 bins.
   - Example 2 Input: `plt.hist([1, 1, 2, 2, 2, 3, 4, 4, 5], bins=5)`
   - Example 2 Expected Output: A histogram with 5 bins.
     - Plots a histogram of the data with 5 bins.

5. **xlabel**
   - Usage: `plt.xlabel(xlabel, fontdict=None, labelpad=None, **kwargs)`
   - Explanation: Sets the label for the x-axis.
   - Example 1 Input: `plt.xlabel('X-axis Label')`
   - Example 1 Expected Output: X-axis is labeled 'X-axis Label'.
     - Sets the x-axis label to the specified string.
   - Example 2 Input: `plt.xlabel('Time (s)', fontsize=14)`
   - Example 2 Expected Output: X-axis labeled 'Time (s)' with font size 14.
     - Sets the x-axis label to 'Time (s)' with the specified font size.

6. **ylabel**
   - Usage: `plt.ylabel(ylabel, fontdict=None, labelpad=None, **kwargs)`
   - Explanation: Sets the label for the y-axis.
   - Example 1 Input: `plt.ylabel('Y-axis Label')`
   - Example 1 Expected Output: Y-axis is labeled 'Y-axis Label'.
     - Sets the y-axis label to the specified string.
   - Example 2 Input: `plt.ylabel('Amplitude', fontsize=14)`
   - Example 2 Expected Output: Y-axis labeled 'Amplitude' with font size 14.
     - Sets the y-axis label to 'Amplitude' with the specified font size.

7. **title**
   - Usage: `plt.title(label, fontdict=None, loc='center', pad=None, **kwargs)`
   - Explanation: Sets the title of the plot.
   - Example 1 Input: `plt.title('Plot Title')`
   - Example 1 Expected Output: Plot is titled 'Plot Title'.
     - Sets the plot title to the specified string.
   - Example 2 Input: `plt.title('Main Plot', fontsize=16)`
   - Example 2 Expected Output: Plot titled 'Main Plot' with font size 16.
     - Sets the plot title to 'Main Plot' with the specified font size.

8. **legend**
   - Usage: `plt.legend(*args, **kwargs)`
   - Explanation: Adds a legend to the plot.
   - Example 1 Input: `plt.legend(['Line 1', 'Line 2'])`
   - Example 1 Expected Output: Legend with labels 'Line 1' and 'Line 2'.
     - Adds a legend with the specified labels.
   - Example 2 Input:
     ```python
     plt.plot([1, 2, 3], label='Line 1')
     plt.plot([4, 5, 6], label='Line 2')
     plt.legend()
     ```
   - Example 2 Expected Output: Legend with labels 'Line 1' and 'Line 2' corresponding to the plots.
     - Automatically adds a legend with labels from the plot commands.

9. **axhline**
   - Usage: `plt.axhline(y=0, xmin=0, xmax=1, **kwargs)`
   - Explanation: Adds a horizontal line across the plot.
   - Example 1 Input: `plt.axhline(y=0.5, color='r', linestyle='--')`
   - Example 1 Expected Output: A red dashed horizontal line at y=0.5.
     - Draws a horizontal line at y=0.5 with specified color and linestyle.
   - Example 2 Input: `plt.axhline(y=2, color='b')`
   - Example 2 Expected Output: A blue horizontal line at y=2.
     - Draws a horizontal line at y=2 with specified color.

10. **tight_layout**
    - Usage: `plt.tight_layout(pad=1.08, h_pad=None, w_pad=None, rect=None)`
    - Explanation: Adjusts subplots to fit into the figure area.
    - Example 1 Input: `plt.tight_layout()`
    - Example 1 Expected Output: Adjusts layout to fit plots nicely.
      - Adjusts the subplot parameters to give specified padding.
    - Example 2 Input: `plt.tight_layout(pad=2.0)`
    - Example 2 Expected Output: Adjusts layout with padding of 2.0.
      - Adjusts the subplot parameters with specified padding.

11. **suptitle**
    - Usage: `plt.suptitle(t, **kwargs)`
    - Explanation: Adds a title to the figure.
    - Example 1 Input: `plt.suptitle('Main Title')`
    - Example 1 Expected Output: Figure titled 'Main Title'.
      - Adds a main title to the figure.
    - Example 2 Input: `plt.suptitle('Overall Title', fontsize=18)`
    - Example 2 Expected Output: Figure titled 'Overall Title' with font size 18.
      - Adds a main title to the figure with specified font size.

12. **subplot**
    - Usage: `plt.subplot(nrows, ncols, index, **kwargs)`
    - Explanation: Adds a subplot to the current figure.
    - Example 1 Input:
      ```python
      plt.subplot(2, 1, 1)
      plt.plot([1, 2, 3])
      plt.subplot(2, 1, 2)
      plt.plot([4, 5, 6])
      ```
    - Example 1 Expected Output: Two subplots, one above the other.
      - Adds two subplots vertically stacked in a single figure.
    - Example 2 Input:
      ```python
      plt.subplot(1, 2, 1)
      plt.plot([1, 2, 3])
      plt.subplot(1, 2, 2)
      plt.plot([4, 5, 6])
      ```
    - Example 2 Expected Output: Two subplots side by side.
      - Adds two subplots horizontally stacked in a single figure.

13. **savefig**
    - Usage: `plt.savefig(fname, dpi=None, facecolor='w', edgecolor='w', orientation='portrait', ...`
    - Explanation: Saves the current figure to a file.
    - Example 1 Input: `plt.savefig('figure.png')`
    - Example 1 Expected Output: Saves the figure as a PNG file.
      - Saves the current figure to 'figure.png'.
    - Example 

2 Input: `plt.savefig('figure.pdf', dpi=300)`
    - Example 2 Expected Output: Saves the figure as a PDF file with 300 DPI.
      - Saves the current figure to 'figure.pdf' with specified resolution.

14. **scatter**
    - Usage: `plt.scatter(x, y, s=None, c=None, marker=None, cmap=None, norm=None, vmin=None, vmax=None, ...`
    - Explanation: Creates a scatter plot of y vs. x with varying marker size and/or color.
    - Example 1 Input: `plt.scatter([1, 2, 3], [4, 5, 6])`
    - Example 1 Expected Output: Scatter plot of points (1,4), (2,5), (3,6).
      - Creates a scatter plot with specified x and y values.
    - Example 2 Input: `plt.scatter([1, 2, 3], [4, 5, 6], c='r')`
    - Example 2 Expected Output: Red scatter plot of points (1,4), (2,5), (3,6).
      - Creates a scatter plot with specified x and y values, with red markers.

15. **bar**
    - Usage: `plt.bar(x, height, width=0.8, bottom=None, *, align='center', data=None, **kwargs)`
    - Explanation: Makes a bar plot.
    - Example 1 Input: `plt.bar([1, 2, 3], [4, 5, 6])`
    - Example 1 Expected Output: Bar plot with heights 4, 5, and 6 at x positions 1, 2, and 3.
      - Creates a bar plot with specified x positions and heights.
    - Example 2 Input: `plt.bar([1, 2, 3], [4, 5, 6], width=0.5, color='g')`
    - Example 2 Expected Output: Green bar plot with narrower bars.
      - Creates a bar plot with specified x positions, heights, and bar width/color.

16. **barh**
    - Usage: `plt.barh(y, width, height=0.8, left=None, *, align='center', **kwargs)`
    - Explanation: Makes a horizontal bar plot.
    - Example 1 Input: `plt.barh([1, 2, 3], [4, 5, 6])`
    - Example 1 Expected Output: Horizontal bar plot with lengths 4, 5, and 6 at y positions 1, 2, and 3.
      - Creates a horizontal bar plot with specified y positions and lengths.
    - Example 2 Input: `plt.barh([1, 2, 3], [4, 5, 6], height=0.5, color='b')`
    - Example 2 Expected Output: Blue horizontal bar plot with narrower bars.
      - Creates a horizontal bar plot with specified y positions, lengths, and bar height/color.

17. **pie**
    - Usage: `plt.pie(x, explode=None, labels=None, colors=None, autopct=None, pctdistance=0.6, shadow=False, ...`
    - Explanation: Plots a pie chart.
    - Example 1 Input: `plt.pie([10, 20, 30])`
    - Example 1 Expected Output: Pie chart with three slices of sizes 10, 20, and 30.
      - Creates a simple pie chart with specified slice sizes.
    - Example 2 Input: `plt.pie([10, 20, 30], labels=['A', 'B', 'C'], autopct='%1.1f%%')`
    - Example 2 Expected Output: Pie chart with labeled slices and percentage labels.
      - Creates a pie chart with specified slice sizes, labels, and percentage formatting.

In the examples above, the explanations cover what each function does, how to use it, and what the expected output is, along with a brief description of the output. If you need further details or more functions, feel free to ask!