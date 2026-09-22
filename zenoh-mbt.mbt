///|
/// An opaque native Zenoh session.
pub type Session

///|
extern "C" fn session_open_ffi() -> Session = "zenoh_mbt_session_open"

///|
#borrow(session)
extern "C" fn session_close_ffi(session : Session) -> Int = "zenoh_mbt_session_close"

///|
#borrow(session, key, payload)
extern "C" fn session_put_ffi(
  session : Session,
  key : String,
  payload : Bytes,
) -> Int = "zenoh_mbt_session_put"

///|
/// Open a Zenoh session with the default configuration.
pub fn open() -> Session {
  session_open_ffi()
}

///|
/// Close a session and release its native resources.
pub fn Session::close(self : Session) -> Int {
  session_close_ffi(self)
}

///|
/// Publish bytes to a key expression.
pub fn Session::put(self : Session, key : String, payload : Bytes) -> Int {
  session_put_ffi(self, key, payload)
}
