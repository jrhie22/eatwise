export async function getCities(req, res) {
  res.json({
    cities: [
      { label: 'New York City', latitude: 40.7128, longitude: -74.006 },
      { label: 'Los Angeles', latitude: 34.0522, longitude: -118.2437 },
      { label: 'Chicago', latitude: 41.8781, longitude: -87.6298 },
      { label: 'Houston', latitude: 29.7604, longitude: -95.3698 },
      { label: 'Miami', latitude: 25.7617, longitude: -80.1918 }
    ]
  });
}
