/**
 * Datos mock/estáticos — Entrega 1.
 *
 * CERO llamadas a backend real: todo lo que consumen las pantallas sale de
 * aquí. Los IDs están enlazados a mano para que los tabs de detalle de
 * cliente (membresía / pagos / rutina / dieta / progreso) cuenten una
 * historia consistente, como si viniera de una base de datos real.
 *
 * En Entrega 2 este archivo se reemplaza por llamadas a la API; las
 * pantallas no deberían necesitar cambios de forma, solo de origen de datos.
 */
import type {
  AuditLog,
  BodyProgress,
  ClientProfile,
  DietAssignment,
  DietPlan,
  Exercise,
  Membership,
  MembershipPlan,
  MembershipPlanName,
  Notification,
  Payment,
  Routine,
  RoutineAssignment,
  RoutineExercise,
  User,
} from '../types/models'
import { getMembershipDisplayStatus, type MembershipDisplayStatus } from '../utils/membership'

/**
 * "Hoy" narrativo del set de datos mock (Entrega 1): las notificaciones de
 * vencimiento y los ingresos del mes están escritos alrededor de esta fecha.
 * Se pasa explícitamente a los cálculos de vencimiento para que la demo sea
 * determinística sin importar cuándo se abra la app de verdad. En Entrega 2,
 * al conectar al backend real, esto desaparece y se usa `new Date()`.
 */
export const MOCK_TODAY = new Date('2025-09-12T09:00:00')

// ---------------------------------------------------------------------------
// 1. Users (admin, entrenadores, clientes)
// ---------------------------------------------------------------------------
export const users: User[] = [
  { id: 1, full_name: 'Marisol Aragón', email: 'marisol@strongeraragon.mx', password_hash: '$2b$mock', role: 'admin', is_active: true, created_at: '2024-01-10T08:00:00Z' },
  { id: 2, full_name: 'Diego Herrera', email: 'diego.herrera@strongeraragon.mx', password_hash: '$2b$mock', role: 'entrenador', is_active: true, created_at: '2024-02-01T08:00:00Z' },
  { id: 3, full_name: 'Paola Nuñez', email: 'paola.nunez@strongeraragon.mx', password_hash: '$2b$mock', role: 'entrenador', is_active: true, created_at: '2024-02-15T08:00:00Z' },
  { id: 10, full_name: 'Karla Jiménez', email: 'karla.jimenez@gmail.com', password_hash: '$2b$mock', role: 'cliente', is_active: true, created_at: '2025-03-01T08:00:00Z' },
  { id: 11, full_name: 'Luis Ángel Torres', email: 'luisangel.torres@gmail.com', password_hash: '$2b$mock', role: 'cliente', is_active: true, created_at: '2025-04-12T08:00:00Z' },
  { id: 12, full_name: 'Fernanda Casillas', email: 'fer.casillas@gmail.com', password_hash: '$2b$mock', role: 'cliente', is_active: true, created_at: '2025-05-20T08:00:00Z' },
  { id: 13, full_name: 'Rodrigo Bautista', email: 'rodrigo.bautista@gmail.com', password_hash: '$2b$mock', role: 'cliente', is_active: true, created_at: '2025-06-02T08:00:00Z' },
  { id: 14, full_name: 'Ximena Cordero', email: 'ximena.cordero@gmail.com', password_hash: '$2b$mock', role: 'cliente', is_active: true, created_at: '2025-07-18T08:00:00Z' },
  { id: 15, full_name: 'Iván Salgado', email: 'ivan.salgado@gmail.com', password_hash: '$2b$mock', role: 'cliente', is_active: false, created_at: '2024-11-09T08:00:00Z' },
]

export const findUser = (id: number): User | undefined => users.find((u) => u.id === id)

// ---------------------------------------------------------------------------
// 2. ClientProfile
// ---------------------------------------------------------------------------
export const clientProfiles: ClientProfile[] = [
  { id: 100, user_id: 10, trainer_id: 2, phone: '55 1234 5670', birth_date: '1996-03-14', address: 'Av. 510 #212, San Juan de Aragón', emergency_contact: 'Rocío Jiménez - 55 1234 9911', created_at: '2025-03-01T08:10:00Z' },
  { id: 101, user_id: 11, trainer_id: 2, phone: '55 2233 4455', birth_date: '1990-11-02', address: 'Calle Oriente 158, Aragón La Villa', emergency_contact: 'Marta Torres - 55 2233 0099', created_at: '2025-04-12T09:00:00Z' },
  { id: 102, user_id: 12, trainer_id: 3, phone: '55 3344 5566', birth_date: '2000-07-22', address: 'Av. 412 #88, San Juan de Aragón 4ta Sección', emergency_contact: 'Hugo Casillas - 55 3344 1122', created_at: '2025-05-20T10:30:00Z' },
  { id: 103, user_id: 13, trainer_id: null, phone: '55 4455 6677', birth_date: '1985-01-30', address: 'Calle 546 #34, Aragón Inguarán', emergency_contact: 'Brenda Bautista - 55 4455 0033', created_at: '2025-06-02T07:45:00Z' },
  { id: 104, user_id: 14, trainer_id: 3, phone: '55 5566 7788', birth_date: '1998-09-09', address: 'Av. 675 #19, San Juan de Aragón 6ta Sección', emergency_contact: 'Noé Cordero - 55 5566 4400', created_at: '2025-07-18T16:20:00Z' },
  { id: 105, user_id: 15, trainer_id: 2, phone: '55 6677 8899', birth_date: '1993-05-17', address: 'Calle 522 #7, Aragón La Villa', emergency_contact: 'Diana Salgado - 55 6677 2233', created_at: '2024-11-09T08:30:00Z' },
]

export const findClientProfile = (id: number): ClientProfile | undefined =>
  clientProfiles.find((c) => c.id === id)

export const getClientDisplayName = (clientId: number): string => {
  const profile = findClientProfile(clientId)
  if (!profile) return 'Cliente desconocido'
  return findUser(profile.user_id)?.full_name ?? 'Cliente desconocido'
}

export const getTrainerDisplayName = (trainerId: number | null): string => {
  if (trainerId === null) return 'Sin asignar'
  return findUser(trainerId)?.full_name ?? 'Sin asignar'
}

// ---------------------------------------------------------------------------
// 3. MembershipPlan (Básica / VIP / Premium)
// ---------------------------------------------------------------------------
export const membershipPlans: MembershipPlan[] = [
  {
    id: 1,
    name: 'Básica',
    description: 'Acceso a piso de pesas y cardio en horario general.',
    price: 399,
    duration_days: 30,
    benefits: ['Acceso a piso de pesas', 'Zona de cardio', 'Casillero diario'],
  },
  {
    id: 2,
    name: 'VIP',
    description: 'Acceso ampliado más una rutina personalizada al mes.',
    price: 649,
    duration_days: 30,
    benefits: ['Todo lo de Básica', '1 rutina personalizada al mes', 'Clases grupales', 'Casillero fijo'],
  },
  {
    id: 3,
    name: 'Premium',
    description: 'Acceso total con seguimiento nutricional y de entrenador dedicado.',
    price: 999,
    duration_days: 30,
    benefits: ['Todo lo de VIP', 'Plan de dieta personalizado', 'Entrenador asignado', 'Evaluación de progreso quincenal'],
  },
]

export const findMembershipPlan = (id: number): MembershipPlan | undefined =>
  membershipPlans.find((p) => p.id === id)

// ---------------------------------------------------------------------------
// 4. Membership
// ---------------------------------------------------------------------------
export const memberships: Membership[] = [
  // status = 'activa': "por vencer" no es un estado propio, se calcula sobre
  // end_date vs. MOCK_TODAY (ver utils/membership.ts y DECISIONES.md).
  { id: 900, client_id: 100, plan_id: 3, start_date: '2025-08-15', end_date: '2025-09-14', status: 'activa', created_at: '2025-08-15T09:00:00Z' },
  { id: 901, client_id: 101, plan_id: 2, start_date: '2025-08-01', end_date: '2025-08-31', status: 'vencida', created_at: '2025-08-01T09:00:00Z' },
  { id: 902, client_id: 102, plan_id: 1, start_date: '2025-09-01', end_date: '2025-10-01', status: 'activa', created_at: '2025-09-01T09:00:00Z' },
  { id: 903, client_id: 103, plan_id: 2, start_date: '2025-09-05', end_date: '2025-10-05', status: 'activa', created_at: '2025-09-05T09:00:00Z' },
  { id: 904, client_id: 104, plan_id: 3, start_date: '2025-08-20', end_date: '2025-09-19', status: 'activa', created_at: '2025-08-20T09:00:00Z' },
  { id: 905, client_id: 105, plan_id: 1, start_date: '2025-07-01', end_date: '2025-07-31', status: 'cancelada', created_at: '2025-07-01T09:00:00Z' },
]

export const findMembershipByClient = (clientId: number): Membership | undefined =>
  memberships.find((m) => m.client_id === clientId)

/** Estado a mostrar en UI (incluye `por_vencer` calculado), usando MOCK_TODAY. */
export const getMembershipDisplayStatusMock = (membership: Membership): MembershipDisplayStatus =>
  getMembershipDisplayStatus(membership, MOCK_TODAY)

// ---------------------------------------------------------------------------
// 5. Payment
// ---------------------------------------------------------------------------
export const payments: Payment[] = [
  { id: 700, membership_id: 900, amount: 999, payment_date: '2025-08-15', method: 'tarjeta', status: 'completado', registered_by: 1, notes: null },
  { id: 701, membership_id: 901, amount: 649, payment_date: '2025-08-01', method: 'efectivo', status: 'completado', registered_by: 1, notes: null },
  { id: 702, membership_id: 902, amount: 399, payment_date: '2025-09-01', method: 'transferencia', status: 'completado', registered_by: 1, notes: 'Pago de reinscripción' },
  { id: 703, membership_id: 903, amount: 649, payment_date: '2025-09-05', method: 'tarjeta', status: 'pendiente', registered_by: 1, notes: 'Transferencia en validación' },
  { id: 704, membership_id: 904, amount: 999, payment_date: '2025-08-20', method: 'efectivo', status: 'completado', registered_by: 1, notes: null },
  { id: 705, membership_id: 900, amount: 100, payment_date: '2025-08-16', method: 'efectivo', status: 'completado', registered_by: 1, notes: 'Ajuste por promoción de temporada' },
  { id: 706, membership_id: 905, amount: 399, payment_date: '2025-07-01', method: 'efectivo', status: 'rechazado', registered_by: 1, notes: 'Cliente canceló a media membresía' },
]

export const getPaymentsForMembership = (membershipId: number): Payment[] =>
  payments.filter((p) => p.membership_id === membershipId)

// ---------------------------------------------------------------------------
// 6. Exercise (catálogo)
// ---------------------------------------------------------------------------
export const exercises: Exercise[] = [
  { id: 1, name: 'Sentadilla con barra', muscle_group: 'Pierna', equipment: 'Barra olímpica', description: 'Sentadilla trasera, rango completo, control en la bajada.' },
  { id: 2, name: 'Press de banca', muscle_group: 'Pecho', equipment: 'Barra + banco plano', description: 'Agarre medio, escápulas retraídas.' },
  { id: 3, name: 'Peso muerto rumano', muscle_group: 'Posterior de pierna', equipment: 'Barra olímpica', description: 'Bisagra de cadera, rodillas semi-flexionadas.' },
  { id: 4, name: 'Dominadas', muscle_group: 'Espalda', equipment: 'Barra fija', description: 'Agarre prono, rango completo.' },
  { id: 5, name: 'Press militar', muscle_group: 'Hombro', equipment: 'Barra o mancuernas', description: 'De pie, core activo, sin arquear lumbar.' },
  { id: 6, name: 'Zancadas caminando', muscle_group: 'Pierna', equipment: 'Mancuernas', description: 'Paso amplio, rodilla trasera casi al piso.' },
  { id: 7, name: 'Remo con barra', muscle_group: 'Espalda', equipment: 'Barra olímpica', description: 'Torso a 45°, jalar hacia el ombligo.' },
  { id: 8, name: 'Plancha abdominal', muscle_group: 'Core', equipment: 'Peso corporal', description: 'Cadera neutra, glúteo activo, 3 series al fallo técnico.' },
  { id: 9, name: 'Curl de bíceps', muscle_group: 'Brazo', equipment: 'Mancuernas', description: 'Codo fijo, sin balanceo.' },
  { id: 10, name: 'Elíptica', muscle_group: 'Cardio', equipment: 'Máquina elíptica', description: 'Intervalos de 2 min moderado / 1 min alto.' },
]

export const findExercise = (id: number): Exercise | undefined => exercises.find((e) => e.id === id)

// ---------------------------------------------------------------------------
// 7. Routine
// ---------------------------------------------------------------------------
export const routines: Routine[] = [
  { id: 1, name: 'Fuerza — Full Body A', description: 'Rutina de fuerza de cuerpo completo, 3 días por semana.', created_by: 2, created_at: '2025-01-15T08:00:00Z' },
  { id: 2, name: 'Hipertrofia — Push/Pull/Legs', description: 'Split de 6 días orientado a volumen.', created_by: 2, created_at: '2025-02-10T08:00:00Z' },
  { id: 3, name: 'Acondicionamiento general', description: 'Rutina de baja carga para clientes nuevos.', created_by: 3, created_at: '2025-03-05T08:00:00Z' },
  { id: 4, name: 'Premium — Fuerza + Core', description: 'Rutina para plan Premium, incluye trabajo de core dedicado.', created_by: 3, created_at: '2025-04-01T08:00:00Z' },
]

export const findRoutine = (id: number): Routine | undefined => routines.find((r) => r.id === id)

// ---------------------------------------------------------------------------
// 8. RoutineExercise (tabla puente Routine <-> Exercise)
// ---------------------------------------------------------------------------
export const routineExercises: RoutineExercise[] = [
  { id: 1, routine_id: 1, exercise_id: 1, sets: 4, reps: 8, rest_seconds: 90, order: 1, notes: null },
  { id: 2, routine_id: 1, exercise_id: 2, sets: 4, reps: 8, rest_seconds: 90, order: 2, notes: null },
  { id: 3, routine_id: 1, exercise_id: 7, sets: 3, reps: 10, rest_seconds: 60, order: 3, notes: null },
  { id: 4, routine_id: 1, exercise_id: 8, sets: 3, reps: 45, rest_seconds: 45, order: 4, notes: 'Reps = segundos sostenidos' },
  { id: 5, routine_id: 4, exercise_id: 3, sets: 4, reps: 8, rest_seconds: 90, order: 1, notes: null },
  { id: 6, routine_id: 4, exercise_id: 5, sets: 4, reps: 6, rest_seconds: 120, order: 2, notes: null },
  { id: 7, routine_id: 4, exercise_id: 6, sets: 3, reps: 12, rest_seconds: 60, order: 3, notes: 'Por pierna' },
  { id: 8, routine_id: 4, exercise_id: 8, sets: 3, reps: 60, rest_seconds: 45, order: 4, notes: 'Reps = segundos sostenidos' },
  { id: 9, routine_id: 3, exercise_id: 10, sets: 1, reps: 20, rest_seconds: 0, order: 1, notes: 'Minutos continuos' },
  { id: 10, routine_id: 3, exercise_id: 9, sets: 3, reps: 12, rest_seconds: 45, order: 2, notes: null },
  { id: 11, routine_id: 2, exercise_id: 2, sets: 4, reps: 10, rest_seconds: 75, order: 1, notes: 'Día push' },
  { id: 12, routine_id: 2, exercise_id: 5, sets: 3, reps: 10, rest_seconds: 75, order: 2, notes: 'Día push' },
  { id: 13, routine_id: 2, exercise_id: 4, sets: 4, reps: 8, rest_seconds: 90, order: 3, notes: 'Día pull' },
  { id: 14, routine_id: 2, exercise_id: 7, sets: 3, reps: 10, rest_seconds: 75, order: 4, notes: 'Día pull' },
  { id: 15, routine_id: 2, exercise_id: 1, sets: 4, reps: 8, rest_seconds: 90, order: 5, notes: 'Día legs' },
  { id: 16, routine_id: 2, exercise_id: 6, sets: 3, reps: 12, rest_seconds: 60, order: 6, notes: 'Día legs, por pierna' },
]

export const getRoutineExercises = (routineId: number): RoutineExercise[] =>
  routineExercises.filter((re) => re.routine_id === routineId).sort((a, b) => a.order - b.order)

// ---------------------------------------------------------------------------
// 9. RoutineAssignment
// ---------------------------------------------------------------------------
export const routineAssignments: RoutineAssignment[] = [
  { id: 500, routine_id: 4, client_id: 100, assigned_by: 3, assigned_date: '2025-08-16', status: 'activa', notes: null },
  { id: 501, routine_id: 2, client_id: 101, assigned_by: 2, assigned_date: '2025-08-02', status: 'activa', notes: null },
  { id: 502, routine_id: 3, client_id: 102, assigned_by: 3, assigned_date: '2025-09-01', status: 'activa', notes: 'Cliente nuevo, revisar técnica primero' },
  { id: 503, routine_id: 1, client_id: 103, assigned_by: 2, assigned_date: '2025-06-10', status: 'completada', notes: null },
  { id: 504, routine_id: 4, client_id: 104, assigned_by: 3, assigned_date: '2025-08-21', status: 'activa', notes: null },
]

export const getRoutineAssignmentsForClient = (clientId: number): RoutineAssignment[] =>
  routineAssignments.filter((ra) => ra.client_id === clientId)

// ---------------------------------------------------------------------------
// 10. DietPlan
// ---------------------------------------------------------------------------
export const dietPlans: DietPlan[] = [
  { id: 1, name: 'Déficit calórico moderado', description: 'Enfocado en pérdida de grasa manteniendo masa muscular.', daily_calories: 1800, created_by: 3, created_at: '2025-01-20T08:00:00Z' },
  { id: 2, name: 'Superávit — ganancia muscular', description: 'Aumento calórico progresivo con alto aporte proteico.', daily_calories: 2600, created_by: 2, created_at: '2025-02-14T08:00:00Z' },
  { id: 3, name: 'Mantenimiento general', description: 'Plan balanceado sin objetivo de cambio de peso.', daily_calories: 2200, created_by: 3, created_at: '2025-03-18T08:00:00Z' },
]

export const findDietPlan = (id: number): DietPlan | undefined => dietPlans.find((d) => d.id === id)

// ---------------------------------------------------------------------------
// 11. DietAssignment
// ---------------------------------------------------------------------------
export const dietAssignments: DietAssignment[] = [
  { id: 600, diet_plan_id: 1, client_id: 100, assigned_by: 3, assigned_date: '2025-08-16', status: 'activa', notes: null },
  { id: 601, diet_plan_id: 2, client_id: 101, assigned_by: 2, assigned_date: '2025-08-02', status: 'activa', notes: null },
  { id: 602, diet_plan_id: 3, client_id: 104, assigned_by: 3, assigned_date: '2025-08-21', status: 'activa', notes: null },
]

export const getDietAssignmentsForClient = (clientId: number): DietAssignment[] =>
  dietAssignments.filter((da) => da.client_id === clientId)

// ---------------------------------------------------------------------------
// 12. BodyProgress — varios registros por cliente para graficar evolución
// ---------------------------------------------------------------------------
export const bodyProgress: BodyProgress[] = [
  // Karla Jiménez (client 100)
  { id: 1, client_id: 100, record_date: '2025-06-01', weight_kg: 68.4, height_cm: 164, body_fat_pct: 29.5, muscle_mass_kg: 43.1, chest_cm: 92, waist_cm: 78, hip_cm: 101, arm_cm: 27, notes: 'Inicio de plan Premium' },
  { id: 2, client_id: 100, record_date: '2025-07-01', weight_kg: 67.1, height_cm: 164, body_fat_pct: 28.1, muscle_mass_kg: 43.6, chest_cm: 91, waist_cm: 76, hip_cm: 100, arm_cm: 27.3, notes: null },
  { id: 3, client_id: 100, record_date: '2025-08-01', weight_kg: 65.9, height_cm: 164, body_fat_pct: 27.0, muscle_mass_kg: 44.0, chest_cm: 90, waist_cm: 74, hip_cm: 99, arm_cm: 27.6, notes: null },
  { id: 4, client_id: 100, record_date: '2025-09-01', weight_kg: 64.8, height_cm: 164, body_fat_pct: 26.2, muscle_mass_kg: 44.3, chest_cm: 90, waist_cm: 73, hip_cm: 98, arm_cm: 28, notes: 'Buena adherencia a la dieta' },
  // Luis Ángel Torres (client 101)
  { id: 5, client_id: 101, record_date: '2025-06-01', weight_kg: 74.2, height_cm: 178, body_fat_pct: 18.4, muscle_mass_kg: 58.9, chest_cm: 99, waist_cm: 83, hip_cm: 96, arm_cm: 33, notes: null },
  { id: 6, client_id: 101, record_date: '2025-07-01', weight_kg: 75.6, height_cm: 178, body_fat_pct: 18.0, muscle_mass_kg: 60.1, chest_cm: 100, waist_cm: 83, hip_cm: 96, arm_cm: 33.6, notes: null },
  { id: 7, client_id: 101, record_date: '2025-08-01', weight_kg: 76.9, height_cm: 178, body_fat_pct: 17.6, muscle_mass_kg: 61.3, chest_cm: 101, waist_cm: 84, hip_cm: 97, arm_cm: 34.2, notes: 'Fase de volumen' },
  // Fernanda Casillas (client 102)
  { id: 8, client_id: 102, record_date: '2025-09-01', weight_kg: 58.0, height_cm: 160, body_fat_pct: 24.8, muscle_mass_kg: 38.4, chest_cm: 85, waist_cm: 68, hip_cm: 92, arm_cm: 24, notes: 'Primera evaluación' },
  // Rodrigo Bautista (client 103)
  { id: 9, client_id: 103, record_date: '2025-06-10', weight_kg: 88.5, height_cm: 172, body_fat_pct: 31.2, muscle_mass_kg: 54.8, chest_cm: 104, waist_cm: 98, hip_cm: 106, arm_cm: 31, notes: null },
  { id: 10, client_id: 103, record_date: '2025-07-10', weight_kg: 86.1, height_cm: 172, body_fat_pct: 29.6, muscle_mass_kg: 55.4, chest_cm: 103, waist_cm: 95, hip_cm: 105, arm_cm: 31.2, notes: null },
  { id: 11, client_id: 103, record_date: '2025-08-10', weight_kg: 84.0, height_cm: 172, body_fat_pct: 28.1, muscle_mass_kg: 55.9, chest_cm: 102, waist_cm: 92, hip_cm: 104, arm_cm: 31.4, notes: null },
  { id: 12, client_id: 103, record_date: '2025-09-10', weight_kg: 82.3, height_cm: 172, body_fat_pct: 27.0, muscle_mass_kg: 56.3, chest_cm: 101, waist_cm: 90, hip_cm: 103, arm_cm: 31.6, notes: 'Sigue en descenso constante' },
  // Ximena Cordero (client 104)
  { id: 13, client_id: 104, record_date: '2025-08-21', weight_kg: 61.5, height_cm: 166, body_fat_pct: 25.4, muscle_mass_kg: 40.2, chest_cm: 88, waist_cm: 71, hip_cm: 96, arm_cm: 25.5, notes: null },
]

export const getBodyProgressForClient = (clientId: number): BodyProgress[] =>
  bodyProgress
    .filter((bp) => bp.client_id === clientId)
    .sort((a, b) => a.record_date.localeCompare(b.record_date))

// ---------------------------------------------------------------------------
// 13. Notification
// ---------------------------------------------------------------------------
export const notifications: Notification[] = [
  { id: 1, user_id: 1, type: 'membresia_vencida', message: 'La membresía de Luis Ángel Torres venció el 31/08/2025.', is_read: false, created_at: '2025-09-01T07:00:00Z' },
  { id: 2, user_id: 1, type: 'membresia_por_vencer', message: 'La membresía de Karla Jiménez vence el 14/09/2025.', is_read: false, created_at: '2025-09-10T07:00:00Z' },
  { id: 3, user_id: 1, type: 'membresia_por_vencer', message: 'La membresía de Ximena Cordero vence el 19/09/2025.', is_read: false, created_at: '2025-09-11T07:00:00Z' },
  { id: 4, user_id: 1, type: 'pago_registrado', message: 'Se registró un pago de $649 de Rodrigo Bautista.', is_read: true, created_at: '2025-09-05T12:00:00Z' },
  { id: 5, user_id: 2, type: 'rutina_asignada', message: 'Se asignó la rutina "Push/Pull/Legs" a Luis Ángel Torres.', is_read: true, created_at: '2025-08-02T09:00:00Z' },
  { id: 6, user_id: 3, type: 'dieta_asignada', message: 'Se asignó el plan "Mantenimiento general" a Ximena Cordero.', is_read: false, created_at: '2025-08-21T09:30:00Z' },
]

export const getNotificationsForUser = (userId: number): Notification[] =>
  notifications.filter((n) => n.user_id === userId)

// ---------------------------------------------------------------------------
// 14. AuditLog
// ---------------------------------------------------------------------------
export const auditLogs: AuditLog[] = [
  { id: 1, user_id: 1, action: 'CREATE', entity_type: 'Membership', entity_id: 900, details: 'Alta de membresía Premium para cliente 100', created_at: '2025-08-15T09:00:00Z' },
  { id: 2, user_id: 1, action: 'CREATE', entity_type: 'Payment', entity_id: 700, details: 'Pago de $999 registrado', created_at: '2025-08-15T09:05:00Z' },
  { id: 3, user_id: 2, action: 'CREATE', entity_type: 'RoutineAssignment', entity_id: 501, details: 'Rutina Push/Pull/Legs asignada', created_at: '2025-08-02T09:00:00Z' },
  { id: 4, user_id: null, action: 'DETECT_EXPIRING', entity_type: 'Membership', entity_id: 900, details: 'Job automático detectó membresía próxima a vencer', created_at: '2025-09-10T06:00:00Z' },
]

// ---------------------------------------------------------------------------
// Helpers agregados para Dashboard / listados
// ---------------------------------------------------------------------------
export const clients = users.filter((u) => u.role === 'cliente')
export const trainers = users.filter((u) => u.role === 'entrenador')

export interface ClientListRow {
  clientProfileId: number
  fullName: string
  email: string
  phone: string
  trainerName: string
  planName: MembershipPlanName | 'Sin membresía'
  membershipStatus: MembershipDisplayStatus | 'sin_membresia'
}

export const clientListRows: ClientListRow[] = clientProfiles.map((profile) => {
  const user = findUser(profile.user_id)
  const membership = findMembershipByClient(profile.id)
  const plan = membership ? findMembershipPlan(membership.plan_id) : undefined
  return {
    clientProfileId: profile.id,
    fullName: user?.full_name ?? 'Cliente desconocido',
    email: user?.email ?? '',
    phone: profile.phone,
    trainerName: getTrainerDisplayName(profile.trainer_id),
    planName: plan?.name ?? 'Sin membresía',
    membershipStatus: membership ? getMembershipDisplayStatusMock(membership) : 'sin_membresia',
  }
})
