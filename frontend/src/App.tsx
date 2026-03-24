import { Header } from "./components/Header";
import { SubmitForm } from "./components/SubmitForm";
import { FeatureList } from "./components/FeatureList";

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-blue-50/30">
      <Header />
      <main className="mx-auto max-w-2xl px-4 pb-16 md:px-6 lg:max-w-3xl lg:px-8">
        <SubmitForm />
        <FeatureList />
      </main>
    </div>
  );
}
