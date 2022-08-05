<?php

namespace ThoughtBundle\Controller\Profile;

use Application\Sonata\UserBundle\Entity\Friendship;
use Application\Sonata\UserBundle\Entity\User;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\ParamConverter;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Form\User\ProfileForm;
use ThoughtBundle\Form\User\UserInfoForm;
use ThoughtBundle\Model\ProfileModel;

/**
 * @Route("/profile")
 */
class SettingsController extends Controller
{

    /**
     * @Route("/settings", name="my_settings")
     * @Route("/student/{user_id}", name="student_profile")
     * @ParamConverter("student", options={"mapping"={"user_id"="id"}})
     * @param Request $request
     * @return Response
     */
    public function mySettings(Request $request, User $student = null)
    {
        $user = $this->getUser();

        if (!is_null($student)) {
            $this->denyAccessUnlessGranted($student, $this->getUser());
            $user = $student;
        }

        $entityManager = $this->container->get('doctrine.orm.entity_manager');
        $formSettings = $this->createForm(new ProfileForm(), $user);
        $formInfo = $this->createForm(new UserInfoForm(), $user);

        $formSettings->handleRequest($request);
        $formInfo->handleRequest($request);

        if ($formSettings->isSubmitted()) {
            if ($formSettings->isValid()) {
                $entityManager->persist($user);
                $entityManager->flush();
            } else {
                $errors   = $this->getErrorMessages($formSettings);
                $messages = $this->errorMessages($errors);
                $this->setFlash('sonata_user_error', $messages);
            }
        }

        if ($formInfo->isSubmitted()) {
            if ($formInfo->isValid()) {
                $entityManager->persist($user);
                $entityManager->flush();
            } else {
                $errors   = $this->getErrorMessages($formInfo);
                $messages = $this->errorMessages($errors);
                $this->setFlash('sonata_user_error', $messages);
            }
        }

        return $this->render('@Thought/Profile/User/settings.html.twig', [
            'user' => $this->getUser(),
            'form_settings' => $formSettings->createView(),
            'form_info' => $formInfo->createView(),
            'student' => $student
        ]);
    }

    /**
     * @Route("/user/{userId}", name="user_profile")
     * @ParamConverter("user", options={"mapping"={"userId"="id"}})
     * @param int $userId
     * @return RedirectResponse|Response
     */
    public function showAction($userId, User $user)
    {
        $this->denyAccessUnlessGranted('view', $user);

        $friendship = $this
            ->getDoctrine()
            ->getRepository(Friendship::class)
            ->isFriend($this->getUser(), $user);

        return $this->render('@Thought/Profile/User/info.html.twig', [
            'user'       => $user,
            'friendship' => $friendship,
        ]);
    }

    /**
     * @Route("/remove", name="remove_profile")
     */
    public function removeAccount()
    {
        /** @var ProfileModel $profileModel */
        $profileModel = $this->container->get('thought.model.profile_model');
        $user = $this->getUser();

        $profileModel->removeAccount($user);
        return $this->redirectToRoute('fos_user_security_login');
    }
}