# Architectural Patterns

Cross-file patterns and conventions used throughout the codebase.

## Backend Patterns

### Modular FastAPI Routers

Routers are registered in `main.py:67-71` with prefixes:

```python
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(events_router, prefix="/api/events", tags=["events"])
app.include_router(sensors_router, prefix="/api/sensors", tags=["sensors"])
app.include_router(ingest_router, prefix="/api/ingest", tags=["ingest"])
```

Each module has its own `router.py`:
- `auth/router.py` - Login, refresh, logout, me
- `events/router.py` - Event queries and timeseries
- `sensors/router.py` - Sensor listing
- `ingest/router.py` - Audio ingestion

### Service Layer Abstraction

Routers delegate to service modules for business logic:

- `events/router.py` → `events/service.py` (lines 16-222)
- `ingest/router.py` → `ingest/service.py` (lines 15-102)
- `sensors/router.py` → `sensors/service.py`

Example in `ingest/service.py:15-102`:
```python
async def process_audio_segment(pcm_bytes: bytes, sensor_id: str, location: str):
    inference = get_inference()           # Get singleton
    result = inference.predict(...)       # ML inference
    write_audio_events(...)               # Database write
    await broadcast_new_event(...)        # WebSocket notify
    return result
```

### Singleton with Lazy Initialization

**Database client** - `db/influx.py:6-47`:
```python
_client: InfluxDBClient | None = None

def get_influx_client() -> InfluxDBClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = InfluxDBClient(url=settings.influxdb_url, ...)
    return _client
```

**ML inference engine** - `inference/model.py:232-265`:
```python
_inference: SoundInference | None = None

def get_inference() -> SoundInference | None:
    return _inference

def init_inference(...) -> SoundInference:
    global _inference
    _inference = SoundInference(...)
    return _inference
```

### Pydantic Settings + LRU Cache

`config.py:6-47`:
```python
class Settings(BaseSettings):
    influxdb_url: str = "http://influxdb:8086"
    influxdb_token: str
    model_path: str = "/app/models/hospital_sound_classifier.pth"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### FastAPI Depends() Injection

`auth/dependencies.py:9-20`:
```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    token = credentials.credentials
    token_data = verify_token(token, token_type="access")
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return User(username=token_data.username)
```

Used in endpoints like `events/router.py:19-26`:
```python
@router.get("", response_model=list[AudioEvent])
async def list_events(
    time_range: str = Query("-1h"),
    current_user: User = Depends(get_current_user),
):
    return get_events(time_range=time_range)
```

### WebSocket ConnectionManager

`events/websocket.py:10-35`:
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

async def broadcast_new_event(event: dict):
    await manager.broadcast({"type": "event", "data": event})
```

### Lifespan Context Manager

`main.py:20-47` - Startup/shutdown lifecycle:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init model, DB connections
    settings = get_settings()
    if model_path.exists():
        init_inference(model_path=str(model_path), ...)

    yield  # App runs

    # Shutdown: cleanup
    close_inference()
    close_influx_client()
```

## Frontend Patterns

### React Context for Auth State

`context/AuthContext.tsx:13-69`:
```typescript
export const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)

  const login = async (username: string, password: string) => {
    const tokens = await apiLogin(username, password)
    localStorage.setItem('access_token', tokens.access_token)
    const user = await getCurrentUser()
    setUser(user)
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
```

### Custom Data Fetching Hooks

`hooks/useEvents.ts:13-161` - Multiple hooks follow this pattern:
```typescript
export function useEvents(filters: EventFilters = {}) {
  const [events, setEvents] = useState<AudioEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchEvents = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await getEvents(filters)
      setEvents(data)
    } catch (err) {
      setError('Failed to fetch events')
    } finally {
      setIsLoading(false)
    }
  }, [filters.time_range, filters.location, filters.event_type])

  useEffect(() => { fetchEvents() }, [fetchEvents])

  return { events, isLoading, error, refetch: fetchEvents }
}
```

Similar hooks: `useEventStats()`, `useLoudnessTimeseries()`, `useEventCountTimeseries()`, `useConfidenceTimeseries()`, `useHeatmap()`

### Axios Interceptors for Auth

`api/client.ts:13-59`:
```typescript
// Request interceptor - add token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor - handle 401 with refresh
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      const response = await axios.post(`${API_URL}/api/auth/refresh`, {
        refresh_token: refreshToken,
      })
      localStorage.setItem('access_token', response.data.access_token)
      return client(originalRequest)  // Retry original
    }
    return Promise.reject(error)
  }
)
```

### WebSocket Hook with Auto-Reconnect

`hooks/useWebSocket.ts:1-84`:
- Connects to `/ws/events` with token auth
- Auto-reconnects on disconnect (3s delay)
- Provides `lastMessage` and `isConnected` state
