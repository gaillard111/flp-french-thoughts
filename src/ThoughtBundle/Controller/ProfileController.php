<?php

namespace ThoughtBundle\Controller;

use Application\Sonata\UserBundle\Form\Type\ProfileInfoType;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;

class ProfileController extends Controller
{
    /**
     * @Route("/profile-info", name="sonata_user_edit_profile_info")
     * @param Request $request
     * @return Response
     * @throws \Doctrine\ORM\OptimisticLockException
     */
    public function editProfileInfoAction(Request $request)
    {
        $user = $this->getUser();

        $form = $this->createForm(new ProfileInfoType(), $user);
        $form->handleRequest($request);
        if ($form->isSubmitted()) {
            if ($form->isValid()) {
                $entityManager = $this->container->get('doctrine.orm.entity_manager');
                $entityManager->persist($user);
                $entityManager->flush();
            } else {
                $errors   = $this->getErrorMessages($form);
                $messages = $this->errorMessages($errors);
                $this->setFlash('sonata_user_error', $messages);
            }
            return $this->redirectToRoute('fos_user_profile_edit');
        }
        return $this->render('@ApplicationSonataUser/Profile/Form/edit_profile_info.html.twig', [
            'form' => $form->createView(),
        ]);
    }
}