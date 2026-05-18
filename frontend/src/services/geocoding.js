const WARSAW_VIEWBOX = '20.851,52.367,21.271,52.097';
const WARSAW_BOUNDS = {
  minLat: 52.097,
  maxLat: 52.367,
  minLng: 20.851,
  maxLng: 21.271,
};

function isInsideWarsaw(lat, lng) {
  return (
    lat >= WARSAW_BOUNDS.minLat
    && lat <= WARSAW_BOUNDS.maxLat
    && lng >= WARSAW_BOUNDS.minLng
    && lng <= WARSAW_BOUNDS.maxLng
  );
}

function belongsToWarsaw(address = {}) {
  const administrativeParts = [
    address.city,
    address.town,
    address.village,
    address.municipality,
    address.county,
    address.state_district,
  ]
    .filter(Boolean)
    .map((value) => value.toLowerCase());

  return administrativeParts.some((value) => value === 'warsaw' || value === 'warszawa');
}

function firstDisplayNamePart(displayName) {
  const [firstPart = displayName] = displayName.split(',');
  return firstPart.trim();
}

function buildAddressLabel(address = {}, displayName = '') {
  const streetName = address.road
    || address.pedestrian
    || address.footway
    || address.path
    || address.cycleway
    || address.square
    || address.residential
    || address.amenity;
  const houseNumber = address.house_number || address.house_name;

  if (streetName && houseNumber) {
    return `${streetName} ${houseNumber}`;
  }

  if (streetName) {
    return streetName;
  }

  if (address.amenity) {
    return address.amenity;
  }

  return firstDisplayNamePart(displayName);
}

function mapGeocodingResult(result) {
  const lat = Number.parseFloat(result.lat);
  const lng = Number.parseFloat(result.lon);

  return {
    id: result.place_id,
    label: result.display_name,
    shortLabel: buildAddressLabel(result.address, result.display_name),
    lat,
    lng,
    address: result.address ?? {},
  };
}

export async function searchWarsawAddresses(query) {
  const trimmedQuery = query.trim();

  if (!trimmedQuery) {
    return [];
  }

  const url = new URL('https://nominatim.openstreetmap.org/search');
  url.searchParams.set('format', 'jsonv2');
  url.searchParams.set('limit', '5');
  url.searchParams.set('countrycodes', 'pl');
  url.searchParams.set('addressdetails', '1');
  url.searchParams.set('bounded', '1');
  url.searchParams.set('viewbox', WARSAW_VIEWBOX);
  url.searchParams.set('q', `${trimmedQuery}, Warsaw`);

  const response = await fetch(url.toString(), {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Unable to find that address right now.');
  }

  const payload = await response.json();

  return payload
    .map(mapGeocodingResult)
    .filter((result) => isInsideWarsaw(result.lat, result.lng) && belongsToWarsaw(result.address));
}

export async function reverseGeocodeWarsawPoint(point) {
  const url = new URL('https://nominatim.openstreetmap.org/reverse');
  url.searchParams.set('format', 'jsonv2');
  url.searchParams.set('addressdetails', '1');
  url.searchParams.set('zoom', '18');
  url.searchParams.set('lat', String(point.lat));
  url.searchParams.set('lon', String(point.lng));

  const response = await fetch(url.toString(), {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Unable to resolve a street name for that point right now.');
  }

  const payload = await response.json();
  return mapGeocodingResult(payload);
}
