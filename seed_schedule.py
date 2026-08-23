#!/usr/bin/env python3
"""
One-off generator that encodes the schedule extracted from
YL2_Aeternos_Schedule_BM1.pdf into data/schedule.json.

This is a DEV helper, not part of the runtime build. It exists so the dates are
computed from (week-Monday + weekday offset) instead of being transcribed by
hand. The shipped source of truth is the JSON it writes; you normally edit that
JSON directly (or regenerate it from a new PDF via the extraction prompt).

Weekday offsets: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5.
"""
import json
from datetime import date, timedelta

WEEKDAY_NAME = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

# (block label as printed-but-corrected, Monday of that week)
WEEKS = {
    "w1":  ("AUGUST 3-8, 2026",            date(2026, 8, 3)),
    "w2":  ("AUGUST 10-15, 2026",          date(2026, 8, 10)),
    "w3":  ("AUGUST 17-22, 2026",          date(2026, 8, 17)),
    "w4":  ("AUGUST 24-29, 2026",          date(2026, 8, 24)),
    "w5":  ("AUGUST 31 - SEPTEMBER 5, 2026", date(2026, 8, 31)),
    "w6":  ("SEPTEMBER 7-12, 2026",        date(2026, 9, 7)),
    "w7":  ("SEPTEMBER 14-19, 2026",       date(2026, 9, 14)),
    "w8":  ("SEPTEMBER 21-26, 2026",       date(2026, 9, 21)),
    # w9/w10 headers on the PDF read "2025" - corrected to 2026 (weekday check).
    "w9":  ("SEPTEMBER 28 - OCTOBER 3, 2026", date(2026, 9, 28)),
    "w10": ("OCTOBER 5-10, 2026 (FIRST BIMONTHLY EXAMINATIONS)", date(2026, 10, 5)),
}

events = []


def ev(week, day, subject, activity, title, start=None, end=None,
       lecturer="", section="ALL", all_day=False, confidence="high", notes=""):
    label, monday = WEEKS[week]
    d = monday + timedelta(days=day)
    src = f"{label.split(',')[0]} / {WEEKDAY_NAME[day]}"
    events.append({
        "subject": subject,
        "activity": activity,
        "title": title,
        "date": d.isoformat(),
        "start": start,
        "end": end,
        "all_day": all_day,
        "lecturer": lecturer,
        "section": section,
        "notes": notes,
        "confidence": confidence,
        "source_ref": src,
    })


# convenience wrappers
def timed(week, day, subject, activity, title, start, end, **kw):
    ev(week, day, subject, activity, title, start=start, end=end, **kw)

def allday(week, day, subject, activity, title, **kw):
    kw.setdefault("confidence", "medium")
    ev(week, day, subject, activity, title, all_day=True, **kw)


# ---------------------------------------------------------------- WEEK 1
timed("w1", 0, "MICRO", "Other", "Holy Mass and Initium", "07:30", "09:30",
      confidence="low", notes="Time approximate; opening ceremony.")
allday("w1", 0, "MICRO", "Independent Study", "Reading assignment: Chapters 1 to 7",
       notes="Positioned in afternoon block; no explicit clock time.")
timed("w1", 1, "PHARMACOLOGY", "Exam", "Diagnostic Exam", "08:00", "09:00")
timed("w1", 1, "PHARMACOLOGY", "Orientation", "Orientation", "09:00", "10:00")
timed("w1", 1, "PHARMACOLOGY", "Lecture", "Lecture on Drug Development and Prescription Writing",
      "10:00", "12:00", lecturer="Dr. Shanida Camomot")
timed("w1", 1, "PHARMACOLOGY", "Independent Study", "Independent study", "13:00", "15:00")
allday("w1", 1, "PREVMED", "Orientation", "Orientation")
timed("w1", 2, "PD", "PD", "General Orientation, Hx taking, Interviewing",
      "09:30", "12:00", lecturer="Dr. Chua Tan", notes="Section A & B")
timed("w1", 2, "PD", "PD", "Comprehensive PE, General Survey and Vital signs",
      "13:00", "17:00", lecturer="Dr. Polloso Go")
allday("w1", 3, "OTHER", "Holiday", "Holiday", notes="Unnamed holiday per schedule (Aug 6).")
timed("w1", 4, "PATHOLOGY", "Lecture", "Adaptation, Cell Injury and Death",
      "07:30", "09:30", lecturer="Dr. Alec Maquiling")
timed("w1", 4, "MICRO", "Lecture", "Orientation; Ch 1-3: Intro, Cell Structure, Classification of Bacteria",
      "13:30", "15:30", lecturer="Dr. Anna Marie Sandoval; Dr. Mark Cuyos")
timed("w1", 4, "MICRO", "Laboratory", "Microscope; Exercise 1 (Bacterial morphology, structure, composition)",
      "15:30", "17:30")
allday("w1", 5, "PSYCHIATRY", "Lecture", "Examination and Diagnosis of the Psychiatric Patient",
       lecturer="Dr. Renato Obra")
allday("w1", 5, "RESEARCH", "Orientation", "Research Orientation")

# ---------------------------------------------------------------- WEEK 2
timed("w2", 0, "PATHOLOGY", "Lecture", "Acute Inflammation", "07:30", "09:30",
      lecturer="Dr. Alec Maquiling")
timed("w2", 0, "PATHOLOGY", "Laboratory", "Adaptation, Cell Injury, Death", "09:30", "11:30",
      lecturer="Lead: Dr. VC")
timed("w2", 0, "MICRO", "Lecture", "Ch 4-5: Growth, Culture Medium", "13:30", "15:30",
      lecturer="Dr. Christian Mosqueda")
timed("w2", 0, "MICRO", "Laboratory", "Exercise 1 (Bacterial morphology, structure, composition)",
      "15:30", "17:30")
timed("w2", 1, "PHARMACOLOGY", "Lecture", "Plenary lecture: Pharmacokinetics", "07:30", "11:30",
      lecturer="Dr. Beethoven Bongon")
timed("w2", 1, "PHARMACOLOGY", "Independent Study", "Independent study", "13:00", "15:00")
allday("w2", 1, "PREVMED", "Lecture", "How to cope with stress", lecturer="Dr. Gerona")
timed("w2", 2, "PD", "PD", "Skills: Skin, Hair, Nails (Lecture); Post-test: Projection Exam",
      "09:30", "11:00", lecturer="Dr. Yapha Lee", notes="Section A & B")
timed("w2", 2, "PD", "PD", "HENT (Lecture)", "12:30", "14:30", lecturer="Dr. Chua Tan")
timed("w2", 2, "PD", "PD", "Checking of Medical Bags; Guided Demo on Vital Signs and HENT",
      "14:30", "17:00")
timed("w2", 3, "PATHOLOGY", "Lecture", "Chronic Inflammation / Tissue Renewal", "07:30", "09:30",
      lecturer="Dr. Alec Maquiling")
timed("w2", 3, "PATHOLOGY", "Laboratory", "Adaptation, Cell Injury, Death", "09:30", "11:30",
      lecturer="Lead: Dr. VC")
timed("w2", 3, "MICRO", "Lecture", "Ch 6: Metabolism; Ch 7: Genetics", "13:30", "15:30",
      lecturer="Dr. Feli Paracuelles")
timed("w2", 3, "MICRO", "Laboratory", "Exercise 1 (Bacterial morphology, structure, composition)",
      "15:30", "17:30")
timed("w2", 4, "PATHOLOGY", "Lecture", "Tissue Renewal, Repair & Regeneration", "07:30", "09:30",
      lecturer="Dr. Chel Moscoso")
timed("w2", 4, "MICRO", "Exam", "Short Quiz 1 (Chapters 1 to 5)", "13:30", "13:45",
      confidence="low", notes="Appears struck-through on the scan; may be cancelled/moved.")
timed("w2", 4, "MICRO", "Lecture", "Immunology Overview; Innate & Adaptive Immunity",
      "13:45", "15:30", lecturer="Dr. Ellan Lyll Salada")
timed("w2", 4, "MICRO", "Laboratory", "Exercise 2 (Differential staining: Gram and Acid Fast)",
      "15:30", "17:30")
allday("w2", 5, "PSYCHIATRY", "Lecture", "Contributions from the Neurosciences",
       lecturer="Dr. Obra")

# ---------------------------------------------------------------- WEEK 3
timed("w3", 0, "PATHOLOGY", "Exam", "Long Exam 1: Adaptation to Regeneration", "08:00", "09:00")
timed("w3", 0, "PATHOLOGY", "Laboratory", "Inflammation & Repair", "09:30", "11:30",
      lecturer="Dr. AM")
timed("w3", 0, "MICRO", "Lecture", "Serology", "13:30", "15:30",
      lecturer="Dr. Feli Rose Paracuelles")
timed("w3", 0, "MICRO", "Laboratory", "Exercise 2 (Differential staining: Gram and Acid Fast)",
      "15:30", "17:30", notes="Also: Lab Discussion - Exercise 1.")
timed("w3", 1, "PHARMACOLOGY", "Lecture", "Plenary lecture: Pharmacodynamics", "07:30", "11:30",
      lecturer="Dr. Beethoven Bongon")
timed("w3", 1, "PHARMACOLOGY", "Lecture", "Plenary lecture: Retroviral agents", "13:00", "15:00",
      lecturer="Dr. Fidji Tambago")
allday("w3", 1, "PREVMED", "Lecture", "Universal Health Care", lecturer="Dr. Canal")
timed("w3", 2, "PD", "PD", "Lecture with Demo: Eyes (Bring medical bag)", "09:00", "12:00",
      lecturer="Dr. Melody Tan Daclan", notes="Section A & B")
timed("w3", 2, "PD", "PD", "Hx Taking", "13:00", "14:30")
timed("w3", 2, "PD", "PD", "Writing of output", "14:30", "16:30")
timed("w3", 3, "PATHOLOGY", "Lecture", "Hemodynamic Disorders", "08:00", "09:00",
      lecturer="Dr. Chel Moscoso")
timed("w3", 3, "PATHOLOGY", "Laboratory", "Inflammation & Repair", "09:30", "11:30",
      lecturer="Dr. AM")
timed("w3", 3, "MICRO", "Lecture", "AMI/CMI", "13:30", "15:30",
      lecturer="Dr. Ellan Lyll Salada")
timed("w3", 3, "MICRO", "Laboratory", "Exercises 3 and 4 (Isolation of Bacteria: Streak plate and Pour plate)",
      "15:30", "17:30")
allday("w3", 4, "OTHER", "Holiday", "Ninoy Aquino Day")
allday("w3", 5, "PSYCHIATRY", "Lecture", "Contributions from the Behavioral and Social Sciences",
       lecturer="Dr. Obra")

# ---------------------------------------------------------------- WEEK 4
timed("w4", 0, "PATHOLOGY", "Lecture", "Thromboembolism, Shock", "07:30", "09:30",
      lecturer="Dr. Alec Maquiling")
timed("w4", 0, "PATHOLOGY", "Laboratory", "Hemodynamic Disorders", "09:30", "11:30",
      lecturer="Lead: Dr. CM")
timed("w4", 0, "MICRO", "Lecture", "Aging, HLA", "13:30", "15:30",
      lecturer="Dr. Feli Rose Paracuelles")
timed("w4", 0, "MICRO", "Laboratory", "Exercises 3 and 4 (Isolation of Bacteria: Streak plate and Pour plate)",
      "15:30", "17:30", notes="Also: Lab Discussion - Exercise 2.")
timed("w4", 1, "PHARMACOLOGY", "Exam", "Long Exam", "08:00", "09:00")
timed("w4", 1, "PHARMACOLOGY", "CBL", "Case based learning: Introduction to Immunity/Inflammation, Immune Globulins and Vaccines",
      "09:30", "11:30", section="A")
timed("w4", 1, "PHARMACOLOGY", "CBL", "Case based learning: Introduction to Immunity/Inflammation, Immune Globulins and Vaccines",
      "13:00", "15:00", section="B")
allday("w4", 1, "PREVMED", "Lecture", "Epidemiology, defining disease normality",
       lecturer="Dr. Gerona")
timed("w4", 2, "PD", "Exam", "Long Exam 1 (Beginning until HEENT)", "09:30", "10:30",
      notes="Section A & B")
timed("w4", 2, "PD", "PD", "Graded Return Demo (V/S, Skin, HEENT)", "13:00", "17:00")
timed("w4", 3, "PATHOLOGY", "Lecture", "Disorders of the Immune System 1", "07:30", "09:30",
      lecturer="Dr. Kathrina Gomez")
timed("w4", 3, "PATHOLOGY", "Laboratory", "Hemodynamic Disorders", "09:30", "11:30",
      lecturer="Lead: Dr. CM")
timed("w4", 3, "MICRO", "Lecture", "Review Basic Immunology", "13:30", "15:30",
      lecturer="Dr. Ellan Lyll Salada")
timed("w4", 3, "MICRO", "Laboratory", "Exercise 5 (Phagocytosis)", "15:30", "17:30")
timed("w4", 4, "PATHOLOGY", "Lecture", "Handouts: Genetic Disorders (selected topics)",
      "07:30", "09:30", lecturer="Dr. Chel Moscoso")
timed("w4", 4, "MICRO", "Exam", "Short Quiz 2 (Chapter 6 to Review of Basic Immunology)",
      "13:30", "13:45")
timed("w4", 4, "MICRO", "Lecture", "Hypersensitivity I and II", "13:45", "15:30",
      lecturer="Dr. Anna Marie Sandoval")
timed("w4", 4, "MICRO", "Laboratory", "Exercises 6,7,8 (Malaria, Typhoid, Treponema pallidum)",
      "15:30", "17:30", notes="Also: Lab Discussion - Exercises 3 and 4.")
allday("w4", 5, "PSYCHIATRY", "Exam", "First Long Exam (Exam of Pt and Contributions)",
       lecturer="Dr. Obra")
allday("w4", 5, "RESEARCH", "Other", "Submission and approval of 3 research topics (1st & 2nd years)")

# ---------------------------------------------------------------- WEEK 5
allday("w5", 0, "OTHER", "Holiday", "National Heroes Day")
timed("w5", 1, "PHARMACOLOGY", "CBL", "Case based learning: Antiviral agents", "08:00", "11:30",
      section="A")
timed("w5", 1, "PHARMACOLOGY", "CBL", "Case based learning: Antiviral agents", "13:00", "15:00",
      section="B")
allday("w5", 1, "PREVMED", "Exam", "Long Exam")
timed("w5", 2, "PD", "PD", "Breast and Axillae Lecture; BSE Graded Demo", "09:30", "11:00",
      lecturer="Dr. Chua Tan", notes="Section A & B")
timed("w5", 2, "PD", "PD", "Thorax and Lungs Lecture; Post-test: Projection/Audio Exam",
      "13:00", "15:00", lecturer="Dr. Polloso Go")
timed("w5", 3, "PATHOLOGY", "Lecture", "Disorders of the Immune System 2", "07:30", "09:30",
      lecturer="Dr. Kathrina Gomez")
timed("w5", 3, "PATHOLOGY", "Laboratory", "Immune System Disorders", "09:30", "11:30",
      lecturer="Lead: Dr. AM")
timed("w5", 3, "MICRO", "Lecture", "Hypersensitivity III and IV", "13:30", "15:30",
      lecturer="Dr. Anna Marie Sandoval")
timed("w5", 3, "MICRO", "Laboratory", "Exercises 9,10,11,12 + Covid 19", "15:30", "17:30",
      notes="Also: Lab Discussion - Dengue, HBs Ag, HCV, HIV, Covid 19 (Exercise 5).")
timed("w5", 4, "PATHOLOGY", "Lecture", "Disorders of the Immune System 3", "07:30", "09:30",
      lecturer="Dr. Vashti Castro")
timed("w5", 4, "PATHOLOGY", "Laboratory", "Immune System Disorders", "09:30", "11:30",
      lecturer="Lead: Dr. AM")
timed("w5", 4, "MICRO", "Exam", "Long Exam 1", "13:30", "14:30")
timed("w5", 4, "MICRO", "Lecture", "Ch 1 Review Basic Immunology; Ch 9 & 10: Pathogenesis of Bacterial Infections, Normal Human Microbiota",
      "14:30", "15:30", lecturer="Dr. Christian Mosqueda", confidence="low",
      notes="Printed times overlap the Long Exam; split here for a clean calendar.")
timed("w5", 4, "MICRO", "Laboratory", "Exercise 13 (Hand washing)", "15:30", "17:30")
allday("w5", 5, "PSYCHIATRY", "Lecture", "Schizophrenia & Other Psychotic Disorders",
       lecturer="Dr. Dana Lim")
allday("w5", 5, "RESEARCH", "Other", "Submission of research question for chosen topic (1st & 2nd years)")

# ---------------------------------------------------------------- WEEK 6
timed("w6", 0, "PATHOLOGY", "Exam", "Long Exam 2: Hemodynamic up to Immune System and Genetic Disorders",
      "08:00", "09:00")
timed("w6", 0, "PATHOLOGY", "Laboratory", "Immune System Disorders", "09:30", "11:30",
      lecturer="Dr. AM")
timed("w6", 0, "MICRO", "Lecture", "Ch 13 & 14: Staphylococcus, Streptococcus", "13:30", "15:30",
      lecturer="Dr. Michele Lim")
timed("w6", 0, "MICRO", "Laboratory", "Exercise 13 (Hand washing)", "15:30", "17:30",
      notes="Also: Lab Discussion - Exercises 6,7,8.")
timed("w6", 1, "PHARMACOLOGY", "Lecture", "General Principles of Antimicrobial Therapy",
      "08:00", "09:00", lecturer="Dr. Tambago")
timed("w6", 1, "PHARMACOLOGY", "CBL", "Case based learning: Penicillins, Cephalosporins and other Beta lactamase",
      "09:00", "12:00", section="A", confidence="medium",
      notes="Section not printed for morning CBL; inferred Section A (afternoon is Section B).")
timed("w6", 1, "PHARMACOLOGY", "CBL", "Case based learning: Penicillins, Cephalosporins and other Beta lactamase",
      "13:00", "15:00", section="B")
allday("w6", 1, "PREVMED", "Lecture", "Disease causation, natural history of disease",
       lecturer="Dr. Gerona")
allday("w6", 2, "OTHER", "Holiday", "Don Sergio Osmena Day")
timed("w6", 3, "PATHOLOGY", "Lecture", "Neoplasia 1", "07:30", "09:30",
      lecturer="Dr. Chel Moscoso")
timed("w6", 3, "PATHOLOGY", "Laboratory", "Neoplasia", "09:30", "11:30", lecturer="Lead: Dr. KG")
timed("w6", 3, "MICRO", "Lecture", "Ch 11 & 12: Spore forming, Non-spore forming", "13:30", "15:30",
      lecturer="Dr. Mark Cuyos")
timed("w6", 3, "MICRO", "Laboratory", "Exercise 14 (Antimicrobial susceptibility test)",
      "15:30", "17:30", notes="Also: Lab Discussion - Exercises 9,10,11,12 + Covid 19.")
timed("w6", 4, "PATHOLOGY", "Independent Study", "Independent Study", "07:30", "09:30")
timed("w6", 4, "MICRO", "Exam", "Lab Quiz 1 (Exercises 1 to Covid 19)", "13:30", "13:45")
timed("w6", 4, "MICRO", "Lecture", "Ch 15: Enterics", "13:45", "15:30",
      lecturer="Dr. Ellan Lyll Salada")
timed("w6", 4, "MICRO", "Laboratory", "Exercise 14 (Antimicrobial susceptibility test)",
      "15:30", "17:30")
allday("w6", 5, "PSYCHIATRY", "Lecture", "Mood Disorders", lecturer="Dr. Maria Leore Igot")

# ---------------------------------------------------------------- WEEK 7
timed("w7", 0, "PATHOLOGY", "Lecture", "Neoplasia 2", "07:30", "09:30",
      lecturer="Dr. Chel Moscoso")
timed("w7", 0, "PATHOLOGY", "Laboratory", "Neoplasia", "09:30", "11:30", lecturer="Lead: Dr. KG")
timed("w7", 0, "MICRO", "Lecture", "Ch 16-17: Pseudomonas, Vibrio", "13:30", "15:30",
      lecturer="Dr. Christian Mosqueda")
timed("w7", 0, "MICRO", "Laboratory", "Exercise 15 (Physical & Chemical Methods of Sterilization & Disinfection)",
      "15:30", "17:30", notes="Also: Lab Discussion - Exercise 13.")
timed("w7", 1, "PHARMACOLOGY", "Lecture", "Antifungal agents", "08:00", "09:00",
      lecturer="Dr. Maratas")
timed("w7", 1, "PHARMACOLOGY", "CBL", "Case based learning: Antifungal Agents", "09:00", "11:00",
      section="A")
timed("w7", 1, "PHARMACOLOGY", "CBL", "Case based learning: Antifungal Agents", "13:00", "15:00",
      section="B")
allday("w7", 1, "PREVMED", "Lecture", "Health promotion", lecturer="Dr. Canal")
timed("w7", 2, "PD", "PD", "Hx Taking", "09:30", "11:00", section="A",
      confidence="medium", notes="Complex split cell.")
timed("w7", 2, "PD", "PD", "Guided demo Thorax and Lungs; Breast", "09:30", "12:30", section="B",
      confidence="medium", notes="Complex split cell.")
timed("w7", 2, "PD", "PD", "Guided demo Thorax and Lungs; Breast", "14:00", "17:00", section="A",
      confidence="medium", notes="Complex split cell.")
timed("w7", 2, "PD", "PD", "Hx Taking", "13:30", "15:00", section="B",
      confidence="medium", notes="Complex split cell.")
timed("w7", 2, "PD", "PD", "Writing of outputs", "15:00", "17:00", section="B",
      confidence="medium", notes="Complex split cell.")
timed("w7", 3, "PATHOLOGY", "Lecture", "Neoplasia 3", "07:30", "09:30",
      lecturer="Dr. Kathrina Gomez")
timed("w7", 3, "PATHOLOGY", "Laboratory", "Neoplasia", "09:30", "11:30", lecturer="Lead: Dr. KG")
timed("w7", 3, "MICRO", "Lecture", "Ch 18 & 19: Haemophilus, Yersinia", "13:30", "15:30",
      lecturer="Dr. Anna Marie Sandoval")
timed("w7", 3, "MICRO", "Laboratory", "Exercise 15 (Physical and Chemical Methods of Sterilization and Disinfection)",
      "15:30", "17:30")
timed("w7", 4, "PATHOLOGY", "Independent Study", "Independent Study", "07:30", "09:30")
timed("w7", 4, "MICRO", "Exam", "Long Exam 2 (Hypersensitivity to Chapter 15)", "13:30", "14:30")
timed("w7", 4, "MICRO", "Lecture", "Ch 20 & 21: Neisseria, Anaerobic", "14:30", "15:30",
      lecturer="Dr. Feli Rose Paracuelles")
timed("w7", 4, "MICRO", "Laboratory", "Exercise 16 (Staphylococcus)", "15:30", "17:30")
allday("w7", 5, "PSYCHIATRY", "Lecture", "Anxiety Disorders", lecturer="Dr. Igot")

# ---------------------------------------------------------------- WEEK 8
timed("w8", 0, "PATHOLOGY", "Lecture", "Neoplasia 4", "07:30", "09:30",
      lecturer="Dr. Kathrina Gomez")
timed("w8", 0, "PATHOLOGY", "Laboratory", "Review for Practical Exam", "09:30", "11:30")
timed("w8", 0, "MICRO", "Lecture", "Ch 22 & 23: Legionella, Mycobacteria", "13:30", "15:30",
      lecturer="Dr. Michelle Lim")
timed("w8", 0, "MICRO", "Laboratory", "Exercise 16 (Staphylococcus)", "15:30", "17:30")
timed("w8", 1, "PHARMACOLOGY", "Exam",
      "Long Exam (Immunity/Inflammation, Vaccines, Antiviral, Antimicrobial Therapy, Penicillins/Cephalosporins/Beta lactamase, Antifungal)",
      "08:00", "09:00")
timed("w8", 1, "PHARMACOLOGY", "Lecture", "Patient Safety Lecture", "09:00", "10:00",
      lecturer="Dr. Viacrucis")
timed("w8", 1, "PHARMACOLOGY", "Lecture", "Perinatal and Pediatric Pharmacology", "13:00", "15:00",
      lecturer="Dr. S. Camomot")
allday("w8", 1, "PREVMED", "Exam", "Long Exam")
timed("w8", 2, "PD", "Exam", "Long Exam 2 (Beginning until Thorax and Lungs)", "09:30", "10:30",
      notes="Section A & B")
timed("w8", 2, "PD", "PD", "Graded Return Demo (Beginning until Thorax and Lungs)", "13:00", "17:00")
timed("w8", 3, "PATHOLOGY", "Lecture", "Handouts: Environmental and Childhood Diseases (selected topics)",
      "07:30", "09:30", lecturer="Dr. Vashti Castro")
timed("w8", 3, "PATHOLOGY", "Laboratory", "Review for Practical Exam", "09:30", "11:30")
timed("w8", 3, "MICRO", "Lecture", "Ch 24 & 25: Spirochetes, Mycoplasma", "13:30", "15:30",
      lecturer="Dr. Feli Rose Paracuelles")
timed("w8", 3, "MICRO", "Laboratory", "Exercise 17 (Streptococcus and Enterococcus)", "15:30", "17:30")
timed("w8", 4, "PATHOLOGY", "Independent Study", "Independent Study", "07:30", "09:30")
timed("w8", 4, "MICRO", "Exam", "Short Quiz 3 (Chapters 16 to 23)", "13:30", "13:45")
timed("w8", 4, "MICRO", "Lecture", "Ch 26 & 27: Rickettsia, Chlamydia", "13:45", "15:30",
      lecturer="Dr. Anna Marie Sandoval")
timed("w8", 4, "MICRO", "Laboratory", "Exercise 17 (Streptococcus and Enterococcus)", "15:30", "17:30")
allday("w8", 5, "PSYCHIATRY", "Exam", "Second Long Examination (Schizophrenia, Mood, Anxiety)")
allday("w8", 5, "RESEARCH", "Other", "Submission of Chapter 1 and 2 (1st & 2nd years)")

# ---------------------------------------------------------------- WEEK 9
timed("w9", 0, "PATHOLOGY", "Exam", "Long Exam 3: Neoplasia to Childhood Diseases", "08:00", "09:00")
timed("w9", 0, "MICRO", "Other", "Case Report", "13:30", "15:30")
timed("w9", 0, "MICRO", "Laboratory", "Exercise 22 (Hair Baiting)", "15:30", "17:30",
      notes="Also: Lab Discussion - Exercises 14 and 15.")
timed("w9", 1, "PHARMACOLOGY", "Independent Study", "Independent Study", "08:00", "11:00")
timed("w9", 1, "OTHER", "Exam", "OSCE (PD / PHARMA / MICRO / PATHO / PREVMED)", "13:00", "17:00",
      confidence="medium", notes="Multi-subject OSCE; beginning until Thorax and Lungs.")
timed("w9", 2, "PD", "PD", "Feedback on Outputs", "09:30", "11:00", lecturer="Dr. Chua Tan",
      notes="Section A & B")
timed("w9", 2, "PD", "PD", "Clinical Reasoning and Assessment; Formulating Impression and Differential Diagnosis",
      "13:00", "15:00", lecturer="Dr. Polloso Go")
allday("w9", 3, "PATHOLOGY", "Exam", "1st BM Practical Exam: Adaptation to Neoplasia",
       notes="No explicit time printed; shown in morning block.")
timed("w9", 3, "MICRO", "Other", "Case Report", "13:30", "15:30")
timed("w9", 3, "MICRO", "Laboratory", "Lab Discussion: Exercise 16", "15:30", "17:30")
timed("w9", 4, "PATHOLOGY", "Independent Study", "Independent Learning", "07:30", "09:30")
timed("w9", 4, "MICRO", "Exam", "Lab Quiz 2 (Exercise 13 to 16)", "13:30", "13:45")
timed("w9", 4, "MICRO", "Laboratory", "Review of exercises/slides; Lab Discussion: Exercise 17",
      "13:45", "17:30")
allday("w9", 5, "PSYCHIATRY", "Exam", "First Bimonthly Exam")

# ---------------------------------------------------------------- WEEK 10
timed("w10", 0, "PATHOLOGY", "Exam", "First Bimonthly Examination: Adaptation to Childhood Diseases",
      "08:00", "10:00")
timed("w10", 1, "PHARMACOLOGY", "Exam", "First Bimonthly Examination", "10:00", "12:00")
allday("w10", 1, "PREVMED", "Exam", "First Bimonthly Examination")
allday("w10", 2, "PD", "Exam", "1st Bimonthly Exam",
       notes="No explicit time printed; shown in morning block.")
timed("w10", 4, "MICRO", "Exam", "Midterm Exam: Written Lecture Exam (Ch 1 to Ch 27, Immunology)",
      "10:00", "12:00")
timed("w10", 4, "MICRO", "Exam", "Practical Laboratory Exam (Microscope to Exercise 17)",
      "13:30", "17:30")
allday("w10", 5, "PSYCHIATRY", "Lecture", "OCD and Related Disorders; Trauma and Stressor Related Disorders",
       lecturer="Dr. Dana Lim")

# ---------------------------------------------------------------- build meta + write
week_blocks = []
for _key, (label, monday) in WEEKS.items():
    saturday = monday + timedelta(days=5)
    week_blocks.append({"label": label, "start": monday.isoformat(), "end": saturday.isoformat()})

doc = {
    "meta": {
        "term": "SY 2026-2027 First Bimonthly",
        "source_title": "University of Cebu College of Medicine Foundation, Inc. - Level 2 Calendar of Activities",
        "week_blocks": week_blocks,
        "review_notes": [
            "Weeks of Sep 28 and Oct 5 print the year as 2025 on the source PDF; corrected to 2026 via the weekday check.",
            "Aug 6 is marked HOLIDAY with no name on the source.",
            "Some Saturday PSYCHIATRY / RESEARCH items and a few morning exams have no printed clock time and are entered as all-day.",
            "A few MICRO Friday blocks print overlapping times (quiz + lecture); split into back-to-back events for a clean calendar.",
            "Week of Sep 16 PD cell is section-split with different times per section; best-effort parse, please verify.",
        ],
    },
    "events": events,
}

with open("data/schedule.json", "w", encoding="utf-8") as f:
    json.dump(doc, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(events)} events to data/schedule.json")
