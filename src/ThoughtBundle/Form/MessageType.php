<?php

namespace ThoughtBundle\Form;

use Application\Sonata\UserBundle\Entity\Message;
use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\SubmitType;
use Symfony\Component\Form\Extension\Core\Type\TextareaType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;

class MessageType extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('message', TextareaType::class, [
                'attr' => [
                    'placeholder' => 'Type a message'
                ]
            ])
            ->add('send', SubmitType::class, [
                'label' => 'user.dialogs.message_submit',
            ]);
    }


    public function getBlockPrefix()
    {
        return 'application_sonata_user_bundle_message_type';
    }
}
