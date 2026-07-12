### simple React Native example demonstrating multiple classes and features. It includes a `Button`, `ScrollView`, `View`, `Text`, and fetching data from a free API.

```javascript
import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  Button,
  ActivityIndicator,
} from 'react-native';

const App = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await fetch('https://jsonplaceholder.typicode.com/posts');
      const result = await response.json();
      setData(result.slice(0, 10)); // Get only the first 10 posts
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>React Native Example</Text>
      <Button title="Fetch Data" onPress={fetchData} />
      {loading && <ActivityIndicator size="large" color="#0000ff" />}
      <ScrollView style={styles.scrollView}>
        {data.map((item) => (
          <View key={item.id} style={styles.card}>
            <Text style={styles.cardTitle}>{item.title}</Text>
            <Text>{item.body}</Text>
          </View>
        ))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
  },
  scrollView: {
    marginTop: 20,
  },
  card: {
    backgroundColor: '#fff',
    padding: 15,
    marginVertical: 10,
    borderRadius: 8,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
});

export default App;
```

### Key Features Demonstrated:
- **`View`**: Used as containers for layout.
- **`Text`**: For displaying text content.
- **`ScrollView`**: Allows scrolling through content.
- **`Button`**: Triggers the `fetchData` function.
- **Fetching Data**: Fetches posts from the JSONPlaceholder API.
- **Activity Indicator**: Displays a loading spinner while fetching data.

This example combines multiple core components to provide a functional and interactive interface.