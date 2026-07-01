export const endpoints = {
  billing: {
    account: (accountId: number) => `/billing/accounts/${accountId}`,
    accounts: "/billing/accounts",
    accountByReservation: (reservationId: number) =>
      `/billing/reservations/${reservationId}/account`,
    charges: (accountId: number) =>
      `/billing/accounts/${accountId}/charges`,
    payments: (accountId: number) =>
      `/billing/accounts/${accountId}/payments`,
    status: "/billing/status",
  },
  guests: {
    create: "/guests",
    list: "/guests",
    detail: (guestId: number) => `/guests/${guestId}`,
  },
  reception: {
    events: (reservationId: number) =>
      `/reception/reservations/${reservationId}/events`,
    checkIn: (reservationId: number) =>
      `/reception/reservations/${reservationId}/check-in`,
    checkOut: (reservationId: number) =>
      `/reception/reservations/${reservationId}/check-out`,
    summary: (reservationId: number) =>
      `/reception/reservations/${reservationId}/summary`,
  },
  reservations: {
    cancel: (reservationId: number) =>
      `/reservations/${reservationId}/cancel`,
    create: "/reservations",
    dates: (reservationId: number) =>
      `/reservations/${reservationId}/dates`,
    detail: (reservationId: number) =>
      `/reservations/${reservationId}`,
    list: "/reservations",
    room: (reservationId: number) =>
      `/reservations/${reservationId}/room`,
  },
  rooms: {
    create: "/rooms",
    list: "/rooms",
    detail: (roomId: number) => `/rooms/${roomId}`,
    status: (roomId: number) => `/rooms/${roomId}/status`,
  },
  housekeeping: {
    dirtyRooms: "/housekeeping/dirty-rooms",
  },
  maintenance: {
    repairRooms: "/maintenance/repair-rooms",
  },
  audit: {
    events: "/audit/events",
  },
  system: {
    modules: "/system/modules",
    status: "/system/health",
  },
} as const;
