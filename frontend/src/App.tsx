import { Header } from "./components/Header";
import { SubmitForm } from "./components/SubmitForm";
import { FeatureList } from "./components/FeatureList";

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50">
      <Header />
      <main className="mx-auto max-w-2xl px-4 pb-16">
        <SubmitForm />
        <FeatureList />
      </main>
    </div>
  );
}
