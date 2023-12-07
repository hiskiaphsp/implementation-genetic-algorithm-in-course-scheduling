import pandas as pd
import itertools
import random

class ScheduleGenerator:
    def __init__(self, matakuliah_file, ruangan_file, waktu_file):
        self.matakuliah_df = pd.read_csv(matakuliah_file, delimiter=";")
        self.ruangan_df = pd.read_csv(ruangan_file, delimiter=";")
        self.waktu_df = pd.read_csv(waktu_file, delimiter=";")
        self.days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat']

    def is_time_overlap(self, schedule1, schedule2):
        return not (
            schedule1['Hari'] != schedule2['Hari'] or
            schedule1['Waktu_Akhir'] <= schedule2['Waktu_Mulai'] or
            schedule1['Waktu_Mulai'] >= schedule2['Waktu_Akhir']
        )

    def generate_initial_population(self, population_size):
        population = []
        for _ in range(population_size):
            theory_schedule = {}
            practical_schedule = {}

            # Separate scheduling for theory and practical classes
            for index, row in self.matakuliah_df.iterrows():
                available_days = ['Senin', 'Selasa'] if row['Jenis'] == 'Teori' else ['Selasa', 'Rabu'] if "_P1" in row['Kode'] else ['Kamis', 'Jumat']

                day = random.choice(available_days)

                while (theory_schedule.get(row['Kode']) and theory_schedule[row['Kode']]['Hari'] not in available_days) or \
                      (practical_schedule.get(row['Kode']) and practical_schedule[row['Kode']]['Hari'] not in available_days):
                    day = random.choice(available_days)

                waktu = self.waktu_df[self.waktu_df['Durasi'] == row['Durasi']].sample()
                waktu_mulai = waktu['Waktu_Mulai'].values[0]
                waktu_akhir = waktu['Waktu_Akhir'].values[0]

                ruangan = self.ruangan_df[self.ruangan_df['Jenis'] == row['Jenis']].sample()['Ruangan'].values[0]

                if row['Jenis'] == 'Teori':
                    theory_schedule[row['Kode']] = {'Hari': day, 'Waktu_Mulai': waktu_mulai, 'Waktu_Akhir': waktu_akhir, 'Ruangan': ruangan}
                else:
                    practical_schedule[row['Kode']] = {'Hari': day, 'Waktu_Mulai': waktu_mulai, 'Waktu_Akhir': waktu_akhir, 'Ruangan': ruangan}

            # Merge theory and practical schedules
            schedule = {**theory_schedule, **practical_schedule}
            population.append(schedule)
        return population

    def calculate_fitness(self, schedule):
        fitness = 0
        for pair in itertools.combinations(schedule.keys(), 2):
            if self.is_time_overlap(schedule[pair[0]], schedule[pair[1]]):
                fitness -= 1
        return fitness

    def crossover(self, parent1, parent2):
        crossover_point = len(parent1) // 2
        child = {**dict(list(parent1.items())[:crossover_point]), **dict(list(parent2.items())[crossover_point:])}
        return child

    def mutate(self, schedule):
        mutated_schedule = schedule.copy()
        mutation_course = random.choice(list(mutated_schedule.keys()))

        corresponding_course = mutation_course.replace("_P1", "_P2")

        day = random.choice(['Selasa', 'Rabu'])  # P1 dijadwalkan pada Selasa atau Rabu
        waktu = self.waktu_df[self.waktu_df['Durasi'] == self.matakuliah_df.loc[self.matakuliah_df['Kode'] == mutation_course, 'Durasi'].values[0]].sample()
        waktu_mulai = waktu['Waktu_Mulai'].values[0]
        waktu_akhir = waktu['Waktu_Akhir'].values[0]

        ruangan = self.ruangan_df[self.ruangan_df['Jenis'] == self.matakuliah_df.loc[self.matakuliah_df['Kode'] == mutation_course, 'Jenis'].values[0]].sample()['Ruangan'].values[0]

        initial_start_time = mutated_schedule[mutation_course]['Waktu_Mulai']
        initial_end_time = mutated_schedule[mutation_course]['Waktu_Akhir']

        mutated_schedule[mutation_course] = {'Hari': day, 'Waktu_Mulai': waktu_mulai, 'Waktu_Akhir': waktu_akhir, 'Ruangan': ruangan}

        if "_P2" in mutation_course:
            day_p2 = random.choice(['Kamis', 'Jumat'])
            mutated_schedule[corresponding_course]['Hari'] = day_p2

        return mutated_schedule

    def select_best_individuals(self, population, num_best):
        sorted_population = sorted(population, key=lambda x: self.calculate_fitness(x), reverse=True)
        return sorted_population[:num_best]

    def genetic_algorithm(self, population_size, generations, convergence_threshold=5):
        population = self.generate_initial_population(population_size)
        best_fitness_history = []

        for generation in range(generations):
            selected_population = self.select_best_individuals(population, population_size // 2)

            offspring_population = []
            for i in range(0, len(selected_population), 2):
                parent1 = selected_population[i]
                parent2 = selected_population[i + 1]
                child1 = self.crossover(parent1, parent2)
                child2 = self.crossover(parent2, parent1)
                offspring_population.extend([child1, child2])

            for i in range(len(offspring_population)):
                if random.random() < 0.2:
                    offspring_population[i] = self.mutate(offspring_population[i])

            population = selected_population + offspring_population

            best_fitness = self.calculate_fitness(self.select_best_individuals(population, 1)[0])
            best_fitness_history.append(best_fitness)

            if len(best_fitness_history) > convergence_threshold and all(
                best_fitness == best_fitness_history[-1] for best_fitness in best_fitness_history[-convergence_threshold:]
            ):
                print(f"Converged at generation {generation}")
                break

        best_individual = self.select_best_individuals(population, 1)[0]
        return best_individual

    def format_schedule(self, schedule):
        schedule_list = []
        for course, schedule_info in sorted(schedule.items(), key=lambda x: (self.days.index(x[1]['Hari']), x[1]['Waktu_Mulai'])):
            matakuliah_info = self.matakuliah_df[self.matakuliah_df['Kode'] == course]
            jenis = matakuliah_info['Jenis'].values[0]
            durasi = matakuliah_info['Durasi'].values[0]
            dosen1 = matakuliah_info['Dosen 1'].values[0]
            dosen2 = matakuliah_info['Dosen 2'].values[0]
            asisten_dosen = matakuliah_info['Asisten Dosen'].values[0]
            kelas = matakuliah_info['Kelas'].values[0]
            semester = matakuliah_info['Semester'].values[0]

            schedule_str = f"{schedule_info['Hari']} {schedule_info['Waktu_Mulai']}-{schedule_info['Waktu_Akhir']}"
            ruangan = schedule_info['Ruangan']

            schedule_list.append({
                'course': course,
                'jenis': jenis,
                'durasi': durasi,
                'dosen1': dosen1,
                'dosen2': dosen2,
                'asisten_dosen': asisten_dosen,
                'kelas': kelas,
                'semester': semester,
                'schedule_str': schedule_str,
                'ruangan': ruangan
            })

        return schedule_list

