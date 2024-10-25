# Propozycja Projektu

25.10.2024  
Dawid Kopeć, Dawid Krutul, Maciej Wizerkaniuk.
supressat

<p align="center">
Propozycja projektu:
Detekcja i analiza przejawów występowania botów na platformie Reddit.
</p>

\
**Tło projektu**

Wraz z rosnącą popularnością platform społecznościowych, takich jak Reddit, rośnie również liczba botów, które mogą znacząco wpływać na dyskusję, moderację oraz rozprzestrzenianie informacji. Boty mogą pełnić zarówno pozytywne, jak i negatywne funkcje — od automatycznej moderacji treści po rozprzestrzenianie dezinformacji. Obecnie brak jest skutecznych metod automatycznej identyfikacji oraz analizy wpływu tych botów na społeczności. Projekt ten odpowiada na potrzebę opracowania narzędzi opartych na sztucznej inteligencji, które umożliwią wykrywanie botów oraz analizę ich zachowania, co pozwoli na lepsze zrozumienie ich wpływu na jakość interakcji w mediach cyfrowych.

\
**Naukowe/technologiczne pytania**

1. Czy istnieją charakterystyczne wzorce aktywności, które pozwalają odróżnić boty od ludzkich użytkowników na platformie Reddit?
2. Czy różnice w częstotliwości postowania, czasie reakcji na aktywność lub długości komentarzy mogą być wskaźnikami automatycznych kont?
3. Jakie kluczowe cechy aktywności użytkowników wskazują na bycie botem?
4. Jak duży wpływ mają boty na dynamikę dyskusji na Reddit, zwłaszcza w kontekście moderacji i rozpowszechniania informacji?
5. Czy detekcja botów przy użyciu metod AI/ML, na podstawie danych tekstowych i metadanych (np. liczba upvote'ów, czas publikacji) może osiągnąć skuteczność porównywalną z ręcznym oznaczaniem botów przez moderatorów?

\
**Rezultat końcowy**

Przewidywanym finalnym efektem projektu będzie zaawansowany model Uczenia Maszynowego, zdolny do precyzyjnej detekcji botów na platformie Reddit, wytrenowany na rzeczywistych danych i gotowy do praktycznych zastosowań. Oprócz samego modelu, projekt dostarczy dogłębnej analizy wzorców zachowań botów, identyfikując kluczowe cechy definiujące ich aktywność oraz ich wpływ na interakcje z innymi użytkownikami. Efekty te pozwolą na lepsze zrozumienie roli botów w społecznościach cyfrowych oraz potencjalne zastosowania w moderacji treści i bezpieczeństwie platform internetowych.

\
**Kluczowi interesariusze**  

| Typ interesariusza | Nazwa |
| --- | --- |
| klient | moderatorzy platformy Reddit |
| klient | użytkownicy platformy Reddit |
| klient | użytkownicy innych platform społecznościowych (np. twitter, facebook) |
| sponsor | instytucje naukowo-badawcze |
| sponsor/klient | Firmy zajmujące się detekcją botów |

\
**Dane**  

Dane do realizacji projektu zostaną pozyskane z platformy Reddit za pośrednictwem biblioteki `praw` *(Python Reddit API Wrapper)*, która umożliwia dostęp do publicznych danych z platformy reddit, takich jak posty, komentarze oraz profile użytkowników. Dzięki niej możliwe jest pobranie danych z różnych `subreddits`, zarówno zawierających *"znane boty"*, jak i *"zwykłych użytkowników"*, co pozwoli na uzyskanie realistycznego rozkładu danych. Proces zbierania danych będzie zgodny z polityką Reddit dotyczącą prywatności i API, a dostępność danych została sprawdzona na początkowym etapie projektu, aby upewnić się, że spełniają one wszystkie potrzeby. Na potrzeby zadania projektowego dane pozyskane zostaną z 10 największych społeczności platformy, a także z określonego przedziału czasu.

\
**Plan prac**  

Fazy planu:

1. Pobieranie danych:
   1. Stworzenie skryptu do pobierania danych.
   2. Pobranie danych.
   3. Wstępny preprocessing danych.
2. Oznaczenie pozyskanych danych:
   1. Badanie na temat cech typowych dla botów.
   2. Wytypowanie metod, które pozwolą określić w prosty sposób boty.
   3. Zaimplementowanie wybranych metod.
   4. Oznaczenie danych na podstawie wyników.
3. Trening modelu do detekcji:
   1. Wytypowanie potencjalnych modeli.
   2. Wstępne porównanie i wybranie docelowego modelu.
   3. Wytrenowanie modelu.
   4. Dostosowanie hiperparametrów modelu.
4. Ewaluacja modelu:
   1. Opracowanie planu ewaluacji.
   2. Wytypowanie metryk ewaluacyjnych.
   3. Implementacja oraz przeprowadzenie ewaluacji.
   4. Podsumowanie wyników oraz wnioski.
5. Analizu wpływu cech aktywności.
   1. Wytypowanie kluczowych cech aktywności na podstawie modelu.
   2. Określenie wpływu każdej z wybranych cech.
   3. Identyfikacja *nie oznaczonych* botów.
   4. Analiza wpływu zidentyfikowanych botów na aktywność użytkowników.
- \+ Wisienka na torcie - Efekt końcowy
6. Wizualizacja efektów pracy.
   1. Rozplanowanie plakatu.
   2. Zapisanie najważniejszych elementów.
   3. Sporządzenie wizualizacji wyników.
   4. Złożenie wniosków i wyników w całość.

\
**Kluczowe wskaźniki efektywności (KPI)**

- (08.11.2024) Faza 1: Gotowy skrypt do pobierania danych oraz zebrane dane z 10 największych społeczności Reddit z określonego przedziału czasowego (najpewniej rok).
- (08.11.2024) Faza 2: W pełni oznaczona wyselekcjonowana próbka danych, stanowiąca 1/3 posiadanego zbioru oraz "akceptowalne" (max 7 do 3) zbalansowanie etykiet. Dane te zostaną użyte do treningu oraz ewaluacji.
- (08.11.2024) Faza 3 i 4: Wytrenowany model do detekcji botów posiadający wyniki dla danych treningowych na poziomie minimum:
  - 0.95 miary dokładności,
  - 0.95 miary precyzji,
  - 0.9 miary f1.
- (22.11.2024) Faza 5: Gotowe wizualizacje oraz wnioski posiadające kluczowe cechy aktywności botów oraz ich wagę.
- \+ Wisienka na torcie - Efekt końcowy
- (22.11.2024) Faza 6: Gotowy plakat przedstawiajacy opis oraz wyniki projektu.

\
**Powiązane prace**  

- źródło danych biblioteka [praw](https://praw.readthedocs.io/en/stable/)
- podobny projekt [Reddit-Bot-Detector](https://github.com/MatthewTourond/Reddit-Bot-Detector)
- podobny projekt [reddit-spam-bot-detector](https://github.com/creme332/reddit-spam-bot-detector)
- podobny projekt [Twitter Bot or Not](https://github.com/scrapfishies/twitter-bot-detection)
- opracowanie identyfikacji botów [identifying-trolls-and-bots-on-reddit-with-machine-learning](https://towardsdatascience.com/identifying-trolls-and-bots-on-reddit-with-machine-learning-709da5970af1)
- artykuł naukowy opisujący podobny projekt [Bot Detection in Reddit Political Discussion](https://dl.acm.org/doi/pdf/10.1145/3313294.3313386)
- potencjalne źródło pomysłów [Twitter-Bot Detection Dataset](https://www.kaggle.com/datasets/goyaladi/twitter-bot-detection-dataset)
- dokumentacja potencjalnego modelu [RandomForest](https://scikit-learn.org/1.5/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
- tworzenie interaktywnych wykresów umożliwiających dokładniejszą analizę [Plotly](https://plotly.com/python/)
- biblioteki związane z klasteryzacją jak i klasyfikacją np. [Scikit-learn](https://scikit-learn.org/1.5/index.html)
