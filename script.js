const header = document.querySelector("#site-header");
const progressBar = document.querySelector("#scroll-progress-bar");
const revealElements = document.querySelectorAll(".reveal");
const countdown = document.querySelector("#countdown");
const shareButtons = document.querySelectorAll(".share-trigger");
const toast = document.querySelector("#toast");
const bookingInputs = [...document.querySelectorAll("[data-booking]")];
const bookingCount = document.querySelector("#booking-count");
const bookingProgressBar = document.querySelector("#booking-progress-bar");
const resetChecklist = document.querySelector("#reset-checklist");
const daySections = document.querySelectorAll("[data-section]");
const mobileDayLinks = [...document.querySelectorAll(".mobile-dock a")];
const bookingStorageKey = "hiroshima-trip-bookings-v1";

function updateScrollUI() {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const progress = scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0;
  progressBar.style.width = `${Math.min(progress, 100)}%`;
  header.classList.toggle("scrolled", window.scrollY > 40);
}

window.addEventListener("scroll", updateScrollUI, { passive: true });
updateScrollUI();

if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 },
  );
  revealElements.forEach((element) => revealObserver.observe(element));

  const dayObserver = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!visible) return;
      const activeId = visible.target.dataset.section;
      mobileDayLinks.forEach((link) => {
        link.classList.toggle("active", link.getAttribute("href") === `#${activeId}`);
      });
    },
    { rootMargin: "-25% 0px -55% 0px", threshold: [0.05, 0.2, 0.4] },
  );
  daySections.forEach((section) => dayObserver.observe(section));
} else {
  revealElements.forEach((element) => element.classList.add("is-visible"));
}

function updateCountdown() {
  const tripDate = new Date("2026-08-06T00:00:00+09:00");
  const tripEnd = new Date("2026-08-10T00:00:00+09:00");
  const now = new Date();
  const oneDay = 1000 * 60 * 60 * 24;
  const days = Math.ceil((tripDate - now) / oneDay);

  if (now >= tripDate && now < tripEnd) {
    countdown.textContent = "いま、広島を旅しています";
  } else if (days > 0) {
    countdown.textContent = `旅まで、あと${days}日`;
  } else {
    countdown.textContent = "私たちの広島の思い出";
  }
}

updateCountdown();

let toastTimer;
function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("show"), 2600);
}

async function shareTrip() {
  const shareData = {
    title: "海と祈り、おいしい広島。｜2026 夏",
    text: "二人でめぐる、広島3泊4日の旅のしおり",
    url: window.location.href,
  };

  try {
    if (navigator.share) {
      await navigator.share(shareData);
      return;
    }
    await navigator.clipboard.writeText(window.location.href);
    showToast("旅のしおりのURLをコピーしました");
  } catch (error) {
    if (error.name !== "AbortError") {
      showToast("URLをコピーできませんでした");
    }
  }
}

shareButtons.forEach((button) => button.addEventListener("click", shareTrip));

function readBookings() {
  try {
    return JSON.parse(localStorage.getItem(bookingStorageKey)) || {};
  } catch {
    return {};
  }
}

function saveBookings() {
  const values = Object.fromEntries(
    bookingInputs.map((input) => [input.dataset.booking, input.checked]),
  );
  localStorage.setItem(bookingStorageKey, JSON.stringify(values));
}

function renderBookingProgress() {
  const done = bookingInputs.filter((input) => input.checked).length;
  const total = bookingInputs.length;
  bookingCount.textContent = `${done} / ${total}`;
  bookingProgressBar.style.width = `${(done / total) * 100}%`;
}

const savedBookings = readBookings();
bookingInputs.forEach((input) => {
  const isConfirmed = input.dataset.confirmed === "true";
  input.checked = isConfirmed || Boolean(savedBookings[input.dataset.booking]);
  input.addEventListener("change", () => {
    saveBookings();
    renderBookingProgress();
  });
});
renderBookingProgress();

resetChecklist.addEventListener("click", () => {
  bookingInputs.forEach((input) => {
    input.checked = input.dataset.confirmed === "true";
  });
  localStorage.removeItem(bookingStorageKey);
  renderBookingProgress();
  showToast("予約チェックをリセットしました");
});
